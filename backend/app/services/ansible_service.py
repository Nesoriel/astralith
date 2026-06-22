from dataclasses import dataclass
from pathlib import Path
from typing import Any


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

    def run_module_task(self, inventory: dict[str, Any], playbook: list[dict[str, Any]]) -> AnsibleExecutionResult:
        """执行内置模块生成的 Ansible playbook。

        当前是骨架实现；后续会在这里调用 ansible_runner.run。
        """
        _ = inventory, playbook
        return AnsibleExecutionResult(status="pending", stdout="", stderr="", raw_events=[])
