from backend.app.operation_modules.base import LocalizedText, OperationModule, OperationTask

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

service_manage_module = OperationModule(
    module_key="service_manage",
    name=LocalizedText(zh_CN="服务管理", en_US="Service Management"),
    description=LocalizedText(
        zh_CN="受控的 systemd 服务状态与生命周期任务。",
        en_US="Controlled systemd service status and lifecycle tasks.",
    ),
    tasks=[
        OperationTask(
            "service_status",
            LocalizedText(zh_CN="查看服务状态", en_US="Service Status"),
            LocalizedText(zh_CN="查看指定服务状态。", en_US="Check a service status."),
            _SERVICE_PARAMETER_SCHEMA,
        ),
        OperationTask(
            "service_start",
            LocalizedText(zh_CN="启动服务", en_US="Start Service"),
            LocalizedText(zh_CN="启动指定服务。", en_US="Start a service."),
            _SERVICE_PARAMETER_SCHEMA,
        ),
        OperationTask(
            "service_stop",
            LocalizedText(zh_CN="停止服务", en_US="Stop Service"),
            LocalizedText(zh_CN="停止指定服务。", en_US="Stop a service."),
            _SERVICE_PARAMETER_SCHEMA,
        ),
        OperationTask(
            "service_restart",
            LocalizedText(zh_CN="重启服务", en_US="Restart Service"),
            LocalizedText(zh_CN="重启指定服务。", en_US="Restart a service."),
            _SERVICE_PARAMETER_SCHEMA,
        ),
        OperationTask(
            "service_reload",
            LocalizedText(zh_CN="重载服务", en_US="Reload Service"),
            LocalizedText(zh_CN="重载指定服务。", en_US="Reload a service."),
            _SERVICE_PARAMETER_SCHEMA,
        ),
    ],
)
