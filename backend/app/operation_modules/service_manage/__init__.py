import re
from typing import Any

from backend.app.operation_modules.base import LocalizedText, OperationModule, OperationTask

_SERVICE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.@-]+$")
_SERVICE_PARAMETER_SCHEMA = {
    "service_name": {
        "type": "string",
        "pattern": r"^[a-zA-Z0-9_.@-]+$",
        "description": {
            "zh-CN": "systemd 服务名，例如 nginx 或 sshd。",
            "en-US": "Systemd service name, for example nginx or sshd.",
        },
    }
}
_SERVICE_ACTIONS = {
    "service_status": "status",
    "service_start": "started",
    "service_stop": "stopped",
    "service_restart": "restarted",
    "service_reload": "reloaded",
}


def _build_service_playbook(task_key: str, parameters: dict[str, Any]) -> list[dict[str, Any]]:
    """根据服务任务参数生成受控 systemd playbook。"""
    service_name = str(parameters.get("service_name", ""))
    if not _SERVICE_NAME_PATTERN.fullmatch(service_name):
        raise ValueError("Invalid service_name")

    action = _SERVICE_ACTIONS[task_key]
    module_args: dict[str, Any] = {"name": service_name}
    if action == "status":
        ansible_task = {
            "name": task_key,
            "ansible.builtin.command": f"systemctl status {service_name} --no-pager",
            "changed_when": False,
        }
    else:
        module_args["state"] = action
        ansible_task = {"name": task_key, "ansible.builtin.systemd": module_args}

    return [
        {
            "name": f"Run {task_key}",
            "hosts": "all",
            "gather_facts": False,
            "tasks": [ansible_task],
        }
    ]


def _service_task(
    task_key: str,
    zh_name: str,
    en_name: str,
    zh_description: str,
    en_description: str,
) -> OperationTask:
    """创建服务管理任务定义。"""
    return OperationTask(
        task_key,
        LocalizedText(zh_CN=zh_name, en_US=en_name),
        LocalizedText(zh_CN=zh_description, en_US=en_description),
        _SERVICE_PARAMETER_SCHEMA,
        playbook_builder=lambda parameters, key=task_key: _build_service_playbook(key, parameters),
    )


service_manage_module = OperationModule(
    module_key="service_manage",
    name=LocalizedText(zh_CN="服务管理", en_US="Service Management"),
    description=LocalizedText(
        zh_CN="受控的 systemd 服务状态与生命周期任务。",
        en_US="Controlled systemd service status and lifecycle tasks.",
    ),
    tasks=[
        _service_task("service_status", "查看服务状态", "Service Status", "查看指定服务状态。", "Check a service status."),
        _service_task("service_start", "启动服务", "Start Service", "启动指定服务。", "Start a service."),
        _service_task("service_stop", "停止服务", "Stop Service", "停止指定服务。", "Stop a service."),
        _service_task("service_restart", "重启服务", "Restart Service", "重启指定服务。", "Restart a service."),
        _service_task("service_reload", "重载服务", "Reload Service", "重载指定服务。", "Reload a service."),
    ],
)
