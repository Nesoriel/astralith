from dataclasses import dataclass
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
        self.private_data_dir = Path(private_data_dir)

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
        runner_result = ansible_runner.run(
            private_data_dir=str(self.private_data_dir),
            inventory=inventory,
            playbook=playbook,
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
