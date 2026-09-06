"""

@Time :  
@Author : 4ever
@File : .py

"""
import asyncio
import logging
from datetime import datetime
from app.schemas.chat import ChatRequest,ChatResponse
logger = logging.getLogger(__name__)
async def chat(request: ChatRequest) -> ChatResponse:
    logger.info("开始调用chat接口")
    await asyncio.sleep(1)
    logger.info("调用chat接口结束")
    return ChatResponse(
        responseTime = datetime.now(),
        responseMessage = request.message,
        responseStatus = 200
    )

