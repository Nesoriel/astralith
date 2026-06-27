import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.models.task import AiAnalysisResult, EvidencePack, Task, TaskResult


class AiAnalysisService:
    """基于结构化证据包生成 AI 故障分析结果。

    v0.5.0 先提供确定性的本地分析边界：它把任务结果整理为 Evidence Pack，
    再生成可复核的中文诊断报告。后续接入真实模型时，也必须复用这个边界，
    禁止绕过证据包直接让模型自由发挥。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def build_evidence_pack(self, task_result_id: int) -> EvidencePack:
        """从单条任务结果构建并保存 Evidence Pack。"""
        task_result = self._get_task_result(task_result_id)
        task = self._get_task(task_result.task_id)
        host = self.db.get(Host, task_result.host_id) if task_result.host_id is not None else None
        content = _build_evidence_content(task, task_result, host)
        evidence_pack = EvidencePack(
            task_result_id=task_result.id,
            host_id=task_result.host_id,
            content_json=_serialize_json(content),
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(evidence_pack)
        self.db.commit()
        self.db.refresh(evidence_pack)
        return evidence_pack

    def analyze_task_result(self, task_result_id: int) -> AiAnalysisResult:
        """对单条任务结果生成并保存结构化中文诊断报告。"""
        evidence_pack = self.build_evidence_pack(task_result_id)
        content = json.loads(evidence_pack.content_json)
        report = _build_analysis_report(content)
        analysis = AiAnalysisResult(
            evidence_pack_id=evidence_pack.id,
            summary=report["summary"],
            content_json=_serialize_json(report),
            model_name="local-rule-based-v0.5.0",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def analyze_task(self, task_id: int) -> AiAnalysisResult:
        """选择最需要关注的任务结果并生成分析。"""
        task = self.db.get(Task, task_id)
        if task is None:
            raise ValueError("Task not found")
        statement = select(TaskResult).where(TaskResult.task_id == task_id).order_by(TaskResult.id)
        results = list(self.db.scalars(statement))
        if not results:
            raise ValueError("Task has no results to analyze")
        failed_result = next((result for result in results if result.status != "success"), None)
        return self.analyze_task_result((failed_result or results[0]).id)

    def list_task_analyses(self, task_id: int) -> list[AiAnalysisResult]:
        """返回某个任务关联的全部 AI 分析结果。"""
        statement = (
            select(AiAnalysisResult)
            .join(EvidencePack, EvidencePack.id == AiAnalysisResult.evidence_pack_id)
            .join(TaskResult, TaskResult.id == EvidencePack.task_result_id)
            .where(TaskResult.task_id == task_id)
            .order_by(AiAnalysisResult.id)
        )
        return list(self.db.scalars(statement))

    def _get_task_result(self, task_result_id: int) -> TaskResult:
        """读取任务结果，不存在时抛出业务错误。"""
        task_result = self.db.get(TaskResult, task_result_id)
        if task_result is None:
            raise ValueError("Task result not found")
        return task_result

    def _get_task(self, task_id: int) -> Task:
        """读取任务，不存在时抛出业务错误。"""
        task = self.db.get(Task, task_id)
        if task is None:
            raise ValueError("Task not found")
        return task


def _build_evidence_content(task: Task, task_result: TaskResult, host: Host | None) -> dict[str, Any]:
    """整理供 AI 分析使用的结构化证据。"""
    return {
        "task": {
            "id": task.id,
            "name": task.name,
            "module_key": task.module_key,
            "module_task_key": task.module_task_key,
            "status": task.status,
            "parameters": _safe_load_json(task.parameters_json, {}),
        },
        "task_result": {
            "id": task_result.id,
            "status": task_result.status,
            "started_at": task_result.started_at.isoformat() if task_result.started_at else None,
            "finished_at": task_result.finished_at.isoformat() if task_result.finished_at else None,
        },
        "host": _host_to_evidence(host),
        "signals": {
            "stdout": task_result.stdout or "",
            "stderr": task_result.stderr or "",
            "ansible_events": _safe_load_json(task_result.raw_event_data, []),
        },
        "metadata": {
            "source": "task_result",
            "evidence_warning": "AI analysis must cite evidence and require human review.",
        },
    }


def _host_to_evidence(host: Host | None) -> dict[str, Any] | None:
    """转换主机证据，避免暴露私钥内容。"""
    if host is None:
        return None
    return {
        "id": host.id,
        "name": host.name,
        "ip_address": host.ip_address,
        "ssh_port": host.ssh_port,
        "ssh_user": host.ssh_user,
    }


def _build_analysis_report(evidence: dict[str, Any]) -> dict[str, Any]:
    """根据证据包生成可审核的本地诊断报告。"""
    task = evidence["task"]
    host = evidence.get("host") or {}
    signals = evidence["signals"]
    stderr = str(signals.get("stderr") or "").strip()
    stdout = str(signals.get("stdout") or "").strip()
    evidence_line = _first_non_empty_line(stderr) or _first_non_empty_line(stdout) or "未捕获到明确 stdout/stderr。"
    host_name = host.get("name") or "未知主机"
    risk_level = "medium" if evidence["task_result"]["status"] != "success" else "low"
    possible_causes = _infer_possible_causes(evidence_line, signals.get("ansible_events") or [])
    summary = f"任务 {task['name']} 在{host_name}上执行失败，主要错误信号：{evidence_line}"
    if evidence["task_result"]["status"] == "success":
        summary = f"任务 {task['name']} 在{host_name}上执行成功，可基于证据进行复核。"

    return {
        "summary": summary,
        "risk_level": risk_level,
        "key_evidence": [evidence_line],
        "possible_causes": possible_causes,
        "recommended_steps": [
            "先复核 Evidence Pack 中的 stderr、stdout 与 Ansible 事件，确认错误是否可复现。",
            "在目标主机上使用只读命令检查服务状态、磁盘容量、端口连通性或容器状态。",
            "如需修改配置或重启服务，应创建受控任务并经过人工确认。",
        ],
        "review_notes": [
            "该报告基于结构化证据生成，必须由管理员人工复核后才能采取行动。",
            "不要直接复制执行 AI 建议中的高风险命令；所有变更都应通过受控运维模块或 GitOps 提案。",
        ],
        "source": {
            "task_id": task["id"],
            "task_result_id": evidence["task_result"]["id"],
            "host_id": host.get("id"),
        },
    }


def _infer_possible_causes(evidence_line: str, events: list[dict[str, Any]]) -> list[str]:
    """用确定性规则给出演示友好的可能原因。"""
    text = evidence_line.lower()
    event_names = {str(event.get("event", "")) for event in events}
    causes: list[str] = []
    if "no space" in text or "100%" in text:
        causes.append("磁盘空间可能不足，导致命令、服务或写入操作失败。")
    if "timed out" in text or "unreachable" in event_names or "runner_on_unreachable" in event_names:
        causes.append("目标主机可能网络不可达、SSH 不通或认证配置异常。")
    if "service" in text or "systemctl" in text or "failed" in text:
        causes.append("目标服务可能启动失败，需要检查 systemd 状态与服务日志。")
    if not causes:
        causes.append("当前证据不足以确定单一原因，需要结合更多主机状态与日志继续排查。")
    return causes


def _safe_load_json(raw_value: str | None, fallback: Any) -> Any:
    """安全解析 JSON 字段，解析失败时返回默认值。"""
    if not raw_value:
        return fallback
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return fallback


def _first_non_empty_line(value: str) -> str:
    """提取第一行非空文本作为关键证据摘要。"""
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _serialize_json(value: Any) -> str:
    """序列化 JSON 字段，保留中文用于前端展示。"""
    return json.dumps(value, ensure_ascii=False)
