from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """允许 Pydantic 响应模型直接从 SQLAlchemy ORM 对象读取字段。"""

    model_config = ConfigDict(from_attributes=True)
