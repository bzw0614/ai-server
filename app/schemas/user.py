"""用户相关的 Pydantic 数据结构：定义“数据长什么样 + 是否合法”。"""

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """创建/更新用户共用的字段与校验规则。"""

    username: str = Field(min_length=3, max_length=20)
    email: EmailStr

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        # 判断“包含空格”必须是英文空格 ' '；'' in value 永远为 True
        if " " in value:
            raise ValueError("用户名不能包含空格")
        return value


class UserCreate(UserBase):
    """创建用户的请求体。"""

    password: str


class UserUpdate(UserBase):
    """更新用户的请求体（后续 PUT/PATCH 阶段再接入路由）。"""

    password: str


class UserResponse(UserBase):
    """返回给客户端的数据，注意不要返回 password。"""

    id: int


class UserPage(BaseModel):
    """分页查询结果的统一数据结构。"""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
