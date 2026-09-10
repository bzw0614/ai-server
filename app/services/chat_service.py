"""

@Time :  
@Author : 4ever
@File : .py

"""
import asyncio
import json
import logging
from app.schemas.chat import ChatRequest,ChatResponse
import httpx
from app.config.config import LLM_MODEL,LLM_API_KEY,LLM_BASE_URL
from app.prompts.system import SYSTEM_PROMPT
logger = logging.getLogger(__name__)
async def chat(request: ChatRequest) -> ChatResponse:
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": LLM_MODEL,
        "messages":[
            {
                "role":"system",
                "content":SYSTEM_PROMPT,
            },
            {
                "role":"user",
                "content":request.message,
            }
        ],
        "stream":False
    }

    """
        创建 HTTP 客户端
        把客户端交给 client
        执行缩进里的代码
        执行完后自动关闭 HTTP 客户端
    """
    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=60,
        )

        print("status:", response.status_code)
        print("headers:", response.headers)
        print("text:", response.text)

        response.raise_for_status()
        result = response.json()

    return ChatResponse(
        message = result["choices"][0]["message"]["content"],
    )

async def chat_stream(request: ChatRequest):
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": LLM_MODEL,
        "messages":[
            {
                "role":"system",
                "content":SYSTEM_PROMPT,
            },
            {
                "role":"user",
                "content":request.message,
            }
        ],
        "stream":True
    }

    # 第一层：AsyncClient 创建一个异步 HTTP 客户端。
    async with httpx.AsyncClient() as client:
        # 流式不能用post，post是把响应内容接收完成以后，才把 response 返回给你。
        # 第二层：stream 不要一次性把整个响应读完，而是建立一个流式响应。
        async with client.stream(
            "POST",
            f"{LLM_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=60,
        ) as response:
            # 第三层：aiter_lines  上游每传过来一行，我就拿一行。1
            async for line in response.aiter_lines():
                if line:
                    yield f"{line}\n\n"

