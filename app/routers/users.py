"""users 路由：只负责接收 HTTP 参数、调用 Service、返回结果。"""

from fastapi import APIRouter, HTTPException, Query

from app.schemas.user import UserCreate, UserPage, UserResponse
from app.services import user_service

user_router = APIRouter(prefix="/api", tags=["users"])


@user_router.post("/users", response_model=UserResponse, status_code=201)
def create_user(body: UserCreate) -> UserResponse:
    """Body 参数：FastAPI 自动解析 JSON 并用 UserCreate 校验。"""
    return user_service.create_user(body)


@user_router.get("/users", response_model=UserPage)
def list_users(
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
        description="每页条数，范围 1~100",
    ),
) -> UserPage:
    """Query 参数：page >= 1，1 <= page_size <= 100。"""
    return user_service.list_users(page, page_size)


@user_router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int) -> UserResponse:
    """Path 参数：user_id 声明为 int，传入非整数会得到 422。"""
    user = user_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@user_router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int) -> None:
    """删除用户；REST 约定删除成功后返回 204，无响应体。"""
    deleted = user_service.delete_user_by_id(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="用户不存在")
