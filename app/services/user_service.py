"""users 业务层：先用内存 mock 数据模拟，后续接数据库时只改这里。"""

import logging

from app.schemas.user import UserCreate, UserPage, UserResponse

logger = logging.getLogger(__name__)

# 内存模拟数据（服务重启后会重置）；以后替换成数据库查询即可
_USERS: list[dict] = [
    {"id": 1, "username": "zhangsan", "email": "zhangsan@qq.com", "password": "123456"},
    {"id": 2, "username": "lisi", "email": "lisi@qq.com", "password": "123456"},
]
_NEXT_ID: int = 3


def list_users(page: int, page_size: int) -> UserPage:
    """分页返回用户列表。"""
    start = (page - 1) * page_size
    end = start + page_size
    items = [UserResponse(**user) for user in _USERS[start:end]]
    logger.info(
        "分页查询用户: page=%s, page_size=%s, total=%s",
        page,
        page_size,
        len(_USERS),
    )
    return UserPage(
        items=items,
        total=len(_USERS),
        page=page,
        page_size=page_size,
    )


def create_user(data: UserCreate) -> UserResponse:
    """创建用户，并返回不含 password 的用户信息。"""
    global _NEXT_ID

    user = data.model_dump()
    user["id"] = _NEXT_ID
    _USERS.append(user)
    _NEXT_ID += 1

    logger.info("创建用户成功: id=%s, username=%s", user["id"], data.username)
    return UserResponse(**user)


def get_user_by_id(user_id: int) -> UserResponse | None:
    """按 id 查询用户，不存在时返回 None。"""
    for user in _USERS:
        if user["id"] == user_id:
            logger.info("查询用户成功: id=%s", user_id)
            return UserResponse(**user)

    logger.warning("用户不存在: id=%s", user_id)
    return None


def delete_user_by_id(user_id: int) -> bool:
    """删除用户，成功返回 True，用户不存在返回 False。"""
    for index, user in enumerate(_USERS):
        if user["id"] == user_id:
            _USERS.pop(index)
            logger.info("删除用户成功: id=%s", user_id)
            return True

    logger.warning("删除失败，用户不存在: id=%s", user_id)
    return False
