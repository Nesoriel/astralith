from typing import Any

from pydantic import BaseModel, Field


class LocalizedTextRead(BaseModel):
    zh_CN: str = Field(alias="zh-CN")
    en_US: str = Field(alias="en-US")


class OperationTaskRead(BaseModel):
    task_key: str
    name: LocalizedTextRead
    description: LocalizedTextRead
    parameters: dict[str, Any] = Field(default_factory=dict)


class OperationModuleRead(BaseModel):
    module_key: str
    name: LocalizedTextRead
    description: LocalizedTextRead
    tasks: list[OperationTaskRead]
