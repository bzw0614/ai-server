"""

@Time :  
@Author : 4ever
@File : .py

"""
from datetime import datetime

from pydantic import BaseModel,Field, field_validator
class ChatRequest(BaseModel):
    message: str
    temperature: float = Field(ge=0, le=2)
    # Pydantic v2 必须把 @field_validator 放在外层，@classmethod 放在内层
    @field_validator("message")
    @classmethod
    def validate_message(cls, value):
        if len(value) < 1:
            raise ValueError("用户输入内容不能为空")
        return value

class ChatResponse(BaseModel):
    message: str #回复