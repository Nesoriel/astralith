from backend.app.operation_modules.registry import registry


class OperationModuleService:
    """内置运维模块查询服务。"""

    def list_modules(self):
        """返回当前注册表中的全部内置模块。"""

        return registry.list_modules()
