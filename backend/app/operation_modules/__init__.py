from backend.app.operation_modules.registry import registry
from backend.app.operation_modules.service_manage import service_manage_module
from backend.app.operation_modules.system_inspection import system_inspection_module

registry.register(system_inspection_module)
registry.register(service_manage_module)

__all__ = ["registry"]
