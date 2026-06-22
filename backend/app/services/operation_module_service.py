from backend.app.operation_modules.registry import registry


class OperationModuleService:
    def list_modules(self):
        return registry.list_modules()
