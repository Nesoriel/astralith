from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LocalizedText:
    """中英文双语文本。"""

    zh_CN: str
    en_US: str


@dataclass(frozen=True, slots=True)
class OperationTask:
    """内置运维模块中的一个具体任务。

    例如 system_inspection 模块下的 check_disk，或 service_manage 模块下的
    service_restart。这里先保存元数据，后续再补充 Ansible Runner 执行内容生成。
    """

    task_key: str
    name: LocalizedText
    description: LocalizedText
    parameters: dict[str, Any] = field(default_factory=dict)
    ansible_tasks: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class OperationModule:
    """内置运维模块定义。

    注意：这是受控的内置模块，不是用户可上传的第三方插件。
    """

    module_key: str
    name: LocalizedText
    description: LocalizedText
    tasks: list[OperationTask]

    def get_task(self, task_key: str) -> OperationTask | None:
        """按任务 key 查找模块内的任务。"""
        return next((task for task in self.tasks if task.task_key == task_key), None)
