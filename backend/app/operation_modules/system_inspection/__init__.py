from backend.app.operation_modules.base import LocalizedText, OperationModule, OperationTask

system_inspection_module = OperationModule(
    module_key="system_inspection",
    name=LocalizedText(zh_CN="系统巡检", en_US="System Inspection"),
    description=LocalizedText(
        zh_CN="只读 Linux 系统巡检任务。",
        en_US="Read-only Linux system inspection tasks.",
    ),
    tasks=[
        OperationTask(
            "check_disk",
            LocalizedText(zh_CN="检查磁盘", en_US="Check Disk"),
            LocalizedText(zh_CN="在目标主机执行 df -h。", en_US="Run df -h on target hosts."),
        ),
        OperationTask(
            "check_memory",
            LocalizedText(zh_CN="检查内存", en_US="Check Memory"),
            LocalizedText(zh_CN="在目标主机执行 free -m。", en_US="Run free -m on target hosts."),
        ),
        OperationTask(
            "check_load",
            LocalizedText(zh_CN="检查负载", en_US="Check Load"),
            LocalizedText(zh_CN="在目标主机执行 uptime。", en_US="Run uptime on target hosts."),
        ),
        OperationTask(
            "check_uptime",
            LocalizedText(zh_CN="检查运行时间", en_US="Check Uptime"),
            LocalizedText(zh_CN="查看目标主机运行时间。", en_US="Check target host uptime."),
        ),
        OperationTask(
            "check_logged_users",
            LocalizedText(zh_CN="检查登录用户", en_US="Check Logged Users"),
            LocalizedText(zh_CN="在目标主机执行 who。", en_US="Run who on target hosts."),
        ),
    ],
)
