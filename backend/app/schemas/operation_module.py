from typing import Any

from pydantic import BaseModel, Field


class LocalizedTextRead(BaseModel):
    """API 响应中的中英文双语文本。"""

    zh_CN: str = Field(alias="zh-CN")
    en_US: str = Field(alias="en-US")


class OperationTaskRead(BaseModel):
    """内置运维模块下的单个任务元数据。"""

    task_key: str
    name: LocalizedTextRead
    description: LocalizedTextRead
    parameters: dict[str, Any] = Field(default_factory=dict)


class OperationModuleRead(BaseModel):
    """内置运维模块及其任务列表的 API 响应模型。"""

    module_key: str
    name: LocalizedTextRead
    description: LocalizedTextRead
    tasks: list[OperationTaskRead]
