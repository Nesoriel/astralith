import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.models.gitops import DesiredResource, GitOpsRepository, GitOpsSyncRun
from backend.app.schemas.gitops import DesiredResourceRead, GitOpsRepositoryCreate, GitOpsRepositoryUpdate


class GitOpsService:
    """GitOps 期望状态仓库同步服务。

    v0.6.0 只负责同步、解析和展示 Desired Resources，不执行任何远端变更。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_repositories(self) -> list[GitOpsRepository]:
        """按创建顺序倒序返回 GitOps 仓库配置。"""
        return list(self.db.scalars(select(GitOpsRepository).order_by(GitOpsRepository.id.desc())))

    def get_repository(self, repository_id: int) -> GitOpsRepository | None:
        """按 ID 查询 GitOps 仓库。"""
        return self.db.get(GitOpsRepository, repository_id)

    def create_repository(self, payload: GitOpsRepositoryCreate) -> GitOpsRepository:
        """创建 GitOps 仓库配置。"""
        repository = GitOpsRepository(**payload.model_dump())
        self.db.add(repository)
        self.db.commit()
        self.db.refresh(repository)
        return repository

    def update_repository(
        self,
        repository: GitOpsRepository,
        payload: GitOpsRepositoryUpdate,
    ) -> GitOpsRepository:
        """更新 GitOps 仓库配置。"""
        for field, value in payload.model_dump().items():
            setattr(repository, field, value)
        self.db.commit()
        self.db.refresh(repository)
        return repository

    def list_sync_runs(self, repository_id: int) -> list[GitOpsSyncRun]:
        """返回仓库同步记录。"""
        statement = (
            select(GitOpsSyncRun)
            .where(GitOpsSyncRun.repository_id == repository_id)
            .order_by(GitOpsSyncRun.id.desc())
        )
        return list(self.db.scalars(statement))

    def list_desired_resources(self, repository_id: int) -> list[DesiredResource]:
        """返回仓库最近一次成功同步解析出的 Desired Resources。"""
        statement = (
            select(DesiredResource)
            .where(DesiredResource.repository_id == repository_id)
            .order_by(DesiredResource.resource_type, DesiredResource.resource_key)
        )
        return list(self.db.scalars(statement))

    def sync_repository(self, repository_id: int) -> GitOpsSyncRun:
        """同步 Git 仓库并解析期望状态资源。"""
        repository = self.get_repository(repository_id)
        if repository is None:
            raise ValueError("GitOps repository not found")
        started_at = datetime.now(timezone.utc)
        sync_run = GitOpsSyncRun(
            repository_id=repository.id,
            status="running",
            stdout="",
            stderr="",
            started_at=started_at,
        )
        self.db.add(sync_run)
        self.db.commit()
        self.db.refresh(sync_run)

        try:
            stdout = self._sync_checkout(repository)
            commit_sha = self._git_output(repository.local_path, ["rev-parse", "HEAD"])
            resources = _parse_desired_resources(Path(repository.local_path), commit_sha)
            for resource in resources:
                resource.repository_id = repository.id
            self.db.execute(delete(DesiredResource).where(DesiredResource.repository_id == repository.id))
            self.db.add_all(resources)
            repository.last_sync_at = datetime.now(timezone.utc)
            repository.last_commit_sha = commit_sha
            sync_run.status = "success"
            sync_run.commit_sha = commit_sha
            sync_run.stdout = stdout
            sync_run.stderr = ""
        except Exception as exc:
            sync_run.status = "failed"
            sync_run.stderr = str(exc)
            sync_run.stdout = ""
        finally:
            sync_run.finished_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(sync_run)
        return sync_run

    def desired_resource_to_schema(self, resource: DesiredResource) -> DesiredResourceRead:
        """把 DesiredResource ORM 对象转换为响应模型。"""
        return DesiredResourceRead(
            id=resource.id,
            repository_id=resource.repository_id,
            commit_sha=resource.commit_sha,
            resource_type=resource.resource_type,
            resource_key=resource.resource_key,
            file_path=resource.file_path,
            content=json.loads(resource.content_json),
            content_hash=resource.content_hash,
        )

    def _sync_checkout(self, repository: GitOpsRepository) -> str:
        """克隆或更新本地 checkout。"""
        local_path = Path(repository.local_path)
        if local_path.exists() and not (local_path / ".git").exists():
            raise ValueError(f"Local path exists but is not a Git repository: {local_path}")
        if not local_path.exists():
            local_path.parent.mkdir(parents=True, exist_ok=True)
            result = _run_git(
                ["git", "clone", "--branch", repository.branch, repository.repo_url, str(local_path)]
            )
            return result.stdout
        fetch_result = _run_git(["git", "fetch", "origin", repository.branch], cwd=local_path)
        checkout_result = _run_git(["git", "checkout", repository.branch], cwd=local_path)
        reset_result = _run_git(["git", "reset", "--hard", f"origin/{repository.branch}"], cwd=local_path)
        return fetch_result.stdout + checkout_result.stdout + reset_result.stdout

    def _git_output(self, local_path: str, args: list[str]) -> str:
        """执行 git 命令并返回单行输出。"""
        return _run_git(["git", *args], cwd=Path(local_path)).stdout.strip()


def _run_git(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """运行 git 命令，失败时抛出包含 stderr 的异常。"""
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or f"Git command failed: {command}")
    return result


def _parse_desired_resources(root: Path, commit_sha: str) -> list[DesiredResource]:
    """解析 hosts/stacks/modules/policies 下的 YAML 资源文件。"""
    resources: list[DesiredResource] = []
    resources.extend(_parse_yaml_files(root, commit_sha, "hosts", "host", "*.yaml", _key_from_name_field))
    resources.extend(_parse_yaml_files(root, commit_sha, "stacks", "stack", "*/stack.yaml", _key_from_name_field))
    resources.extend(_parse_yaml_files(root, commit_sha, "modules", "module", "*/module.yaml", _key_from_module_field))
    resources.extend(_parse_yaml_files(root, commit_sha, "policies", "policy", "*.yaml", _key_from_file_stem))
    return resources


def _parse_yaml_files(
    root: Path,
    commit_sha: str,
    directory: str,
    resource_type: str,
    glob_pattern: str,
    key_resolver: Any,
) -> list[DesiredResource]:
    """解析某类 YAML 文件并转换为 DesiredResource。"""
    base_dir = root / directory
    if not base_dir.exists():
        return []
    resources: list[DesiredResource] = []
    for file_path in sorted(base_dir.glob(glob_pattern)):
        if not file_path.is_file():
            continue
        text = file_path.read_text(encoding="utf-8")
        content = _parse_simple_yaml(text)
        relative_path = file_path.relative_to(root).as_posix()
        resource_key = key_resolver(content, file_path)
        content_json = json.dumps(content, ensure_ascii=False, sort_keys=True)
        resources.append(
            DesiredResource(
                commit_sha=commit_sha,
                resource_type=resource_type,
                resource_key=resource_key,
                file_path=relative_path,
                content_json=content_json,
                content_hash=hashlib.sha256(content_json.encode("utf-8")).hexdigest(),
            )
        )
    return resources


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """解析 v0.6.0 需要的简单 key/value YAML，避免为 MVP 增加额外依赖。"""
    content: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        content[key.strip()] = _coerce_scalar(value.strip())
    return content


def _coerce_scalar(value: str) -> Any:
    """把简单 YAML 标量转换为 Python 值。"""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.isdigit():
        return int(value)
    return value.strip('"\'')


def _key_from_name_field(content: dict[str, Any], file_path: Path) -> str:
    """优先使用 name 字段作为资源 key。"""
    return str(content.get("name") or file_path.stem)


def _key_from_module_field(content: dict[str, Any], file_path: Path) -> str:
    """模块资源优先使用 module_key。"""
    return str(content.get("module_key") or content.get("name") or file_path.parent.name)


def _key_from_file_stem(content: dict[str, Any], file_path: Path) -> str:
    """策略资源使用文件名作为 key。"""
    _ = content
    return file_path.stem
