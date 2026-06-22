from backend.app.operation_modules.base import OperationModule


class OperationModuleRegistry:
    """内置运维模块注册表。

    启动时把 system_inspection、service_manage 等模块注册进来，API 层只从这里读取，
    避免动态导入用户代码带来的安全风险。
    """

    def __init__(self) -> None:
        self._modules: dict[str, OperationModule] = {}

    def register(self, module: OperationModule) -> None:
        """注册一个受控的内置运维模块。"""

        # 同 key 注册会覆盖旧模块，便于测试；正式模块 key 应保持唯一。
        self._modules[module.module_key] = module

    def list_modules(self) -> list[OperationModule]:
        """返回所有已注册模块。"""
        return list(self._modules.values())

    def get_module(self, module_key: str) -> OperationModule | None:
        """根据 module_key 获取模块；不存在时返回 None。"""
        return self._modules.get(module_key)


registry = OperationModuleRegistry()
