from fastapi import APIRouter, HTTPException

from backend.app.operation_modules.base import LocalizedText
from backend.app.operation_modules.registry import registry
from backend.app.schemas.operation_module import LocalizedTextRead, OperationModuleRead, OperationTaskRead

router = APIRouter()


def _localized_text_to_schema(text: LocalizedText) -> LocalizedTextRead:
    """把内部双语文本转换为 API 响应模型。"""
    return LocalizedTextRead.model_validate({"zh-CN": text.zh_CN, "en-US": text.en_US})


def _module_to_schema(module_key: str) -> OperationModuleRead:
    """把内部模块对象转换为 API 响应模型。"""
    module = registry.get_module(module_key)
    if module is None:
        raise HTTPException(status_code=404, detail="Operation module not found")
    return OperationModuleRead(
        module_key=module.module_key,
        name=_localized_text_to_schema(module.name),
        description=_localized_text_to_schema(module.description),
        tasks=[
            OperationTaskRead(
                task_key=task.task_key,
                name=_localized_text_to_schema(task.name),
                description=_localized_text_to_schema(task.description),
                parameters=task.parameters,
            )
            for task in module.tasks
        ],
    )


@router.get("", response_model=list[OperationModuleRead])
def list_operation_modules() -> list[OperationModuleRead]:
    """列出所有内置运维模块，用于前端任务选择页面。"""
    return [_module_to_schema(module.module_key) for module in registry.list_modules()]


@router.get("/{module_key}", response_model=OperationModuleRead)
def get_operation_module(module_key: str) -> OperationModuleRead:
    """查看单个内置运维模块详情。"""
    return _module_to_schema(module_key)
