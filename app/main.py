"""应用入口：创建 FastAPI 实例并挂载所有路由。"""

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.system import system_router
from app.routers.users import user_router
from app.routers.chat import chat_router

app = FastAPI()

# 浏览器同源策略会拦截跨域请求，前端单独跑（Vite / 静态服务器）时需要放开 CORS。
# 如果前端直接用本服务托管（见文件末尾的静态资源挂载），同源访问不需要这一段。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 只有 include_router 之后，路由才会真正注册到 app
for router in [user_router, system_router, chat_router]:
    app.include_router(router)

# 静态前端页面（web/index.html、styles.css、app.js）。
# 注意：mount("/") 必须放在 include_router 之后，
# 因为路由是按注册顺序匹配的，挂载到 "/" 会吞掉后面注册的所有路径。
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")


if __name__ == "__main__":
    # 等价于命令行执行：uvicorn app.main:app --reload --port 8000
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
