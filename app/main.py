"""应用入口：创建 FastAPI 实例并挂载所有路由。"""

import uvicorn
from fastapi import FastAPI

from app.routers.system import system_router
from app.routers.users import user_router

app = FastAPI()

# 只有 include_router 之后，路由才会真正注册到 app
for router in [user_router, system_router]:
    app.include_router(router)


if __name__ == "__main__":
    # 等价于命令行执行：uvicorn app.main:app --reload --port 8000
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
