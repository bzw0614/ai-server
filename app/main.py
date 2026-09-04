from fastapi import FastAPI

from app.routers.system import system_router
# uvicorn app.main:app --reload --port 8000
'''
app.main:app = 模块路径 app/main.py + 里面模块级的 FastAPI 实例变量 app。所以 main.py 必须存在 app = FastAPI() 这行。
--reload 是开发模式，改代码自动重启；生产环境不要带。
--port 8000 可以改成别的，端口被占时换 8001 等。
'''
app = FastAPI()
app.include_router(system_router)
