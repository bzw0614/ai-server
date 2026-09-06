"""

@Time :  
@Author : 4ever
@File : .py

"""
from fastapi import APIRouter, Depends
from app.dependencies.common import validate_key
from app.schemas.chat import ChatResponse, ChatRequest
from app.services import chat_service
'''
第一种写法：写在APIRouter里，这样这个router下所有的接口都会携带Depends
第二种写法：写在@chat_router.get
第三种写法：写在app = FastAPI()里面。这样所有的接口都会携带Depends
'''
chat_router = APIRouter(prefix="/api", tags=["chat"],dependencies=[
    Depends(validate_key)
])
# @chat_router.get("/chat",dependencies=[Depends(validate_key)])
@chat_router.post("/chat",response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await chat_service.chat(request)