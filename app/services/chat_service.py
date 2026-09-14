"""

@Time :  
@Author : 4ever
@File : .py

"""
import json

import httpx

from app.config.config import LLM_MODEL, LLM_API_KEY, LLM_BASE_URL
from app.model.user import Base
from app.prompts.system import SYSTEM_PROMPT
from app.schemas.chat import ChatRequest, ChatResponse
from app.tools.query_database import get_user_by_name
from app.tools.weather import get_weather


def _jsonable(value):
    """把工具返回值转成 json.dumps 认得的结构。

    get_user_by_name 返回的是 SQLAlchemy 的 User 对象（或对象列表），
    直接 json.dumps 会报 Object of type User is not JSON serializable，
    所以先按表字段拍平成 dict，再喂给模型。
    """
    if isinstance(value, Base):
        return {c.name: _jsonable(getattr(value, c.name)) for c in value.__table__.columns}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {k: _jsonable(item) for k, item in value.items()}
    return value


async def chat(messages, tools=None, temperature=None):
    """
    调用一次 LLM 的 /chat/completions。
    messages 是完整的对话列表，形如：[{"role": "system", "content": "..."}, ...]
    """
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
    }
    if temperature is not None:
        data["temperature"] = temperature

    if tools:
        # 协议要求 tools 是数组，这里兼容外面传单个 dict 的写法
        data["tools"] = tools if isinstance(tools, list) else [tools]

    """
        创建 HTTP 客户端
        把客户端交给 client
        执行缩进里的代码
        执行完后自动关闭 HTTP 客户端
    """
    print("我发送的请求数据：", json.dumps(data, ensure_ascii=False, indent=2))
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            timeout=60,
        )
        # 4xx/5xx 时把上游的报错打在屏幕上，不然只能看到一个状态码
        if response.is_error:
            print("LLM 接口报错：", response.text)
        response.raise_for_status()

        result = response.json()
        # 把模型返回的原始数据以 JSON 打印出来看
        print("LLM 返回：", json.dumps(result, ensure_ascii=False, indent=2))
        return result


async def agent_chat(request: ChatRequest, tools=None, db=None) -> ChatResponse:
    """带工具调用的对话：模型要工具就执行，把结果喂回去，直到模型给出最终回答。

    db 是路由层用 Depends(get_db) 注入进来的数据库会话：工具函数自己拿不到会话，
    只能由调用方（这里是路由）传下来，否则 get_user_by_name 缺参数直接 TypeError。
    """
    # 对话历史。外层是列表，里面的每个元素是 dict（写成 {} 会变成集合，dict 不可哈希，直接报错）
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": request.message,
        },
    ]

    # 模型可能一直要工具却不给答案，最多来回 3 轮
    for _ in range(3):
        response = await chat(messages, tools, request.temperature)
        message = response["choices"][0]["message"]

        # 模型不需要工具时，回复里根本没有 tool_calls 这个 key，所以用 get
        tool_calls = message.get("tool_calls")

        # 没有工具调用，message["content"] 就是最终答案
        if not tool_calls:
            return ChatResponse(message=message["content"])

        # 协议要求：先把这次「带 tool_calls 的 assistant 回复」放进历史，
        # 再放工具的执行结果，顺序反了上游会报错
        messages.append(
            {
                "role": "assistant",
                "content": message.get("content"),
                "tool_calls": tool_calls,
            }
        )

        # 模型可能一次要求调用多个工具
        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            # 模型给的是 JSON 字符串，比如 '{"city": "北京"}'，要自己转成 dict
            arguments = json.loads(tool_call["function"]["arguments"])

            if function_name == "get_weather":
                result = get_weather(**arguments)
            elif function_name == "get_user_by_name":
                if db is None:
                    result = {"error": "没有数据库会话，查不了用户"}
                else:
                    # 工具函数是 async 的，漏了 await 会拿到协程对象，json.dumps 立刻报错
                    result = await get_user_by_name(db, **arguments)
            else:
                result = {"error": f"未知工具：{function_name}"}
            messages.append(
                {
                    "role": "tool",
                    # 每一个方法调用都会有一个 ID
                    "tool_call_id": tool_call["id"],
                    # default=str 兜底：date/datetime 这类 json 不认的类型转成字符串
                    "content": json.dumps(_jsonable(result), ensure_ascii=False, default=str),
                }
            )

    return ChatResponse(message="工具调用轮次过多，已停止。请换一种问法再试。")


async def chat_stream(request: ChatRequest):
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": request.message,
            },
        ],
        "temperature": request.temperature,
        "stream": True,
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
                    # 流式时上游是一个个分片传过来的，打印出来能看到每个分片长什么样
                    print("流式分片：", line)
                    yield f"{line}\n\n"
