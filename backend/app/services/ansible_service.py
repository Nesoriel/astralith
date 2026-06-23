from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import ansible_runner

from backend.app.models.host import Host


@dataclass(slots=True)
class AnsibleExecutionResult:
    """Ansible Runner 执行结果的内部表示。"""

    status: str
    stdout: str
    stderr: str
    raw_events: list[dict[str, Any]]


class AnsibleService:
    """所有 Ansible Runner 调用都必须经过这个服务层。

    这样可以保证 inventory 生成、日志收集、错误处理和结果保存的逻辑集中管理，
    避免 API 路由直接调用 Ansible Runner。
    """

    def __init__(self, private_data_dir: Path | str = "backend/.runner") -> None:
        # Runner 会把工作目录切到 project 下执行 playbook；使用绝对路径可避免
        # 相对 private_data_dir 在 cwd 变化后被拼成 project/backend/.runner/...。
        self.private_data_dir = Path(private_data_dir).resolve()

    @staticmethod
    def build_inventory(hosts: list[Host]) -> dict[str, Any]:
        """把主机记录转换为 Ansible Runner 可用的 inventory。"""
        inventory_hosts: dict[str, dict[str, Any]] = {}
        for host in hosts:
            inventory_hosts[host.name] = {
                "ansible_host": host.ip_address,
                "ansible_port": host.ssh_port,
                "ansible_user": host.ssh_user,
                "ansible_ssh_private_key_file": host.private_key_path,
            }
        return {"all": {"hosts": inventory_hosts}}

    def run_module_task(
        self,
        inventory: dict[str, Any],
        playbook: list[dict[str, Any]],
    ) -> AnsibleExecutionResult:
        """执行内置模块生成的 Ansible playbook。"""
        self.private_data_dir.mkdir(parents=True, exist_ok=True)
        project_dir = self.private_data_dir / "project"
        project_dir.mkdir(parents=True, exist_ok=True)
        playbook_path = project_dir / "main.json"
        # ansible-runner 的 playbook 参数指向 project 目录内的文件名；直接传 Python
        # 对象会让真实 Runner 去寻找不存在的 main.json，导致页面任务永远失败。
        playbook_path.write_text(json.dumps(playbook, ensure_ascii=False), encoding="utf-8")
        runner_result = ansible_runner.run(
            private_data_dir=str(self.private_data_dir),
            inventory=inventory,
            playbook="main.json",
        )
        stdout = _read_runner_stream(getattr(runner_result, "stdout", ""))
        stderr = _read_runner_stream(getattr(runner_result, "stderr", ""))
        events = list(getattr(runner_result, "events", []) or [])
        return AnsibleExecutionResult(
            status=str(getattr(runner_result, "status", "failed")),
            stdout=stdout,
            stderr=stderr,
            raw_events=events,
        )


def _read_runner_stream(stream: Any) -> str:
    """兼容 Runner 文本流与测试替身对象。"""
    if hasattr(stream, "read"):
        return str(stream.read())
    return str(stream or "")
