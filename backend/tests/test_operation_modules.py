from backend.app.operation_modules import registry


def test_builtin_operation_modules_registered() -> None:
    module_keys = {module.module_key for module in registry.list_modules()}

    assert "system_inspection" in module_keys
    assert "service_manage" in module_keys


def test_operation_module_metadata_is_bilingual() -> None:
    system_module = registry.get_module("system_inspection")

    assert system_module is not None
    assert system_module.name.zh_CN == "系统巡检"
    assert system_module.name.en_US == "System Inspection"
    assert system_module.tasks[0].name.zh_CN
    assert system_module.tasks[0].name.en_US
