"""

@Time :  
@Author : 4ever
@File : .py

"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.tools.tool_definitions import WEATHER_TOOL
from app.schemas.chat import ChatResponse, ChatRequest
from app.services import chat_service
'''
第一种写法：写在APIRouter里，这样这个router下所有的接口都会携带Depends
第二种写法：写在@chat_router.get
第三种写法：写在app = FastAPI()里面。这样所有的接口都会携带Depends
'''
chat_router = APIRouter(prefix="/api", tags=["chat"])
# @chat_router.get("/chat",dependencies=[Depends(validate_key)])
@chat_router.post("/chat",response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # agent_chat 内部会按需调用 WEATHER_TOOL，并返回 ChatResponse 实例；
    # 返回裸字符串的话，FastAPI 的 response_model 校验会直接失败。
    return await chat_service.agent_chat(request,WEATHER_TOOL)

@chat_router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    # 函数名不要也叫 chat，否则模块里同名函数互相覆盖，排查问题时容易被误导。
    return StreamingResponse(
        chat_service.chat_stream(request),
        media_type="text/event-stream",
        # 关掉中间层缓冲，否则代理（nginx 等）会攒够一批才吐给浏览器，流式就变「一次性」
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
