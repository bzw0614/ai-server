

# `ai-server` —— AI 服务后端骨架练习项目

目标不是现在就接大模型，而是先把 **FastAPI 后端工程骨架**练熟。等这个项目完成后，再往里面接 LLM、RAG、Agent，会非常顺。

下面这份可以直接作为你的**项目需求文档 + 编码规范**。

---

# 一、项目目标

实现一个简化版的：

> **AI 服务后端基础平台**

暂时不接真实的大模型 API，只模拟 AI 服务。

通过这个项目掌握：

```text
FastAPI
│
├── 1. 路由 Routing
├── 2. Path 参数
├── 3. Query 参数
├── 4. Body 参数
├── 5. Pydantic 数据校验
├── 6. Depends 依赖注入
├── 7. async / await 异步接口
├── 8. Middleware 中间件
├── 9. 统一日志
├── 10. 统一异常处理
├── 11. 统一响应格式
└── 12. 项目分层
```

最终形成：

```text
客户端
   ↓
Middleware
   ↓
Router
   ↓
Dependency
   ↓
Service
   ↓
模拟 AI 服务
   ↓
Response
```

---

# 二、项目功能

这个项目叫：

```text
ai-server
```

实现下面 5 类功能。

## 1. 系统接口

```text
GET /health
```

返回：

```json
{
    "code": 0,
    "message": "success",
    "data": {
        "status": "ok"
    }
}
```

---

## 2. 用户接口

实现：

```text
POST   /api/users
GET    /api/users
GET    /api/users/{user_id}
DELETE /api/users/{user_id}
```

例如：

```text
POST /api/users
```

创建：

```json
{
    "username": "zhangsan",
    "email": "zhangsan@example.com"
}
```

---

## 3. AI 对话接口

实现：

```text
POST /api/chat
```

请求：

```json
{
    "message": "什么是 FastAPI？",
    "temperature": 0.7
}
```

返回：

```json
{
    "code": 0,
    "message": "success",
    "data": {
        "answer": "这是一个模拟的 AI 回答",
        "model": "mock-model"
    }
}
```

暂时不要接 DeepSeek、OpenAI、通义千问。

自己模拟：

```python
await asyncio.sleep(1)
```

假装 AI 思考了 1 秒。

---

## 4. AI 模型接口

实现：

```text
GET /api/models
GET /api/models/{model_name}
```

例如：

```text
GET /api/models
```

返回：

```json
{
    "code": 0,
    "message": "success",
    "data": [
        {
            "name": "mock-model",
            "provider": "local",
            "status": "available"
        }
    ]
}
```

---

## 5. 日志查询接口

实现：

```text
GET /api/logs
```

支持：

```text
?page=1&page_size=10
```

例如：

```text
GET /api/logs?page=1&page_size=10
```

---

# 三、必须使用的 FastAPI 知识

这个项目不是“能跑就行”。

每一个知识点都必须刻意练习。

---

## ① 路由

必须使用：

```python
@app.get()
@app.post()
@app.delete()
```

并且最终不要把所有接口全部塞进 `main.py`。

要求拆成：

```text
routers/
├── user.py
├── chat.py
├── model.py
└── system.py
```

---

# 四、参数练习要求

你必须分别练习三种参数。

## Path 参数

例如：

```text
GET /api/users/{user_id}
```

代码：

```python
async def get_user(user_id: int):
```

要求：

* `user_id` 必须是整数
* 非整数自动触发 FastAPI 参数校验

---

## Query 参数

例如：

```text
GET /api/users?page=1&page_size=10
```

代码：

```python
async def get_users(
    page: int = 1,
    page_size: int = 10,
):
```

要求：

```text
page >= 1
1 <= page_size <= 100
```

使用 FastAPI 参数校验。

---

## Body 参数

创建用户：

```json
{
    "username": "zhangsan",
    "email": "zhangsan@example.com"
}
```

必须使用 Pydantic。

**禁止：**

```python
request: Request

data = await request.json()
```

这一次要真正使用 FastAPI 的方式。

---

# 五、Pydantic 要求

建立：

```text
schemas/
├── user.py
├── chat.py
└── model.py
```

例如：

```python
class UserCreate(BaseModel):
    username: str
    email: EmailStr
```

要求你至少使用：

```text
BaseModel
Field
EmailStr
Enum
datetime
field_validator
model_validator
```

---

# 六、Pydantic 练习要求

### 用户名

要求：

```text
长度：3～20
不能为空
不能包含空格
```

例如：

```text
zhangsan
```

正确。

```text
a
```

错误。

---

### 邮箱

必须：

```python
email: EmailStr
```

---

### AI temperature

定义：

```text
0.0 <= temperature <= 2.0
```

例如：

```json
{
    "message": "你好",
    "temperature": 0.7
}
```

合法。

```json
{
    "message": "你好",
    "temperature": 3
}
```

非法。

---

# 七、Enum 练习

AI 模型提供商：

```python
class ModelProvider(str, Enum):
    LOCAL = "local"
    OPENAI = "openai"
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
```

模型：

```json
{
    "name": "mock-model",
    "provider": "local"
}
```

---

# 八、依赖注入练习

这个项目必须使用：

```python
Depends()
```

例如创建：

```text
dependencies/
└── common.py
```

实现：

```python
async def get_request_id():
    ...
```

然后：

```python
async def chat(
    request_id: str = Depends(get_request_id)
):
    ...
```

---

# 九、再增加一个 API Key 依赖

模拟 AI 服务需要 API Key。

请求：

```text
POST /api/chat
```

Header：

```text
X-API-Key: test-key
```

使用依赖：

```python
Depends(verify_api_key)
```

要求：

```text
正确：
X-API-Key: test-key

错误：
X-API-Key: abc
```

返回：

```json
{
    "code": 401,
    "message": "API Key 无效",
    "data": null
}
```

---

# 十、异步接口

`/api/chat` 必须：

```python
async def chat():
```

模拟 AI 调用：

```python
await asyncio.sleep(1)
```

禁止：

```python
time.sleep(1)
```

你需要真正理解：

```text
async def
   ↓
coroutine
   ↓
await
   ↓
Event Loop
```

---

# 十一、中间件

项目必须实现一个 HTTP Middleware。

要求记录：

```text
请求时间
请求方法
请求路径
请求状态码
请求耗时
request_id
```

日志类似：

```text
2026-09-04 20:30:01 INFO
request_id=abc123
method=POST
path=/api/chat
status=200
cost=1.002s
```

核心：

```python
@app.middleware("http")
async def logging_middleware(request, call_next):
    ...
```

---

# 十二、request_id

每一次请求生成一个：

```text
UUID
```

例如：

```text
request_id=550e8400-e29b-41d4-a716-446655440000
```

然后：

```text
请求进入
    ↓
Middleware生成request_id
    ↓
日志记录
    ↓
Router
    ↓
Service
    ↓
返回Response
    ↓
Middleware记录耗时
```

响应 Header 中也加入：

```text
X-Request-ID
```

这样以后你排查 AI 服务问题的时候，可以：

```text
request_id
    ↓
找到完整请求日志
    ↓
找到具体异常
    ↓
找到调用链
```

这个习惯非常重要。

---

# 十三、统一异常处理

建立：

```text
exceptions/
└── handlers.py
```

至少处理：

```text
ValidationError
UserNotFoundError
AuthenticationError
ServiceError
Exception
```

最终统一返回：

```json
{
    "code": 404,
    "message": "用户不存在",
    "data": null
}
```

---

# 十四、统一响应格式

整个项目统一：

### 成功

```json
{
    "code": 0,
    "message": "success",
    "data": {}
}
```

### 失败

```json
{
    "code": 400,
    "message": "参数错误",
    "data": null
}
```

你可以实现：

```text
core/
└── response.py
```

里面：

```python
ok()
error()
```

以后业务代码不要到处自己拼：

```python
{
    "code": 0,
    "message": "...",
    "data": ...
}
```

---

# 十五、项目目录规范

最终项目结构要求：

```text
ai-server/
│
├── app/
│   │
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── response.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── system.py
│   │   ├── users.py
│   │   ├── chat.py
│   │   └── models.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── chat.py
│   │   └── model.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── chat_service.py
│   │   └── model_service.py
│   │
│   ├── dependencies/
│   │   ├── __init__.py
│   │   └── common.py
│   │
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── handlers.py
│   │
│   └── middleware/
│       ├── __init__.py
│       └── logging.py
│
├── tests/
│   ├── __init__.py
│   ├── test_users.py
│   ├── test_chat.py
│   └── test_models.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

# 十六、代码编写规范

这个部分我建议你以后**固定下来，不要每个项目换一种写法**。

## 规范 1：文件名

统一：

```text
小写 + 下划线
```

正确：

```text
user_service.py
chat_service.py
response.py
```

不要：

```text
UserService.py
userService.py
```

---

# 十七、函数命名

使用：

```text
动词 + 名词
```

例如：

```python
create_user()
get_user()
list_users()
delete_user()
update_user()
verify_api_key()
get_request_id()
```

不要：

```python
user()
user_data()
do_it()
handle()
```

---

# 十八、Router 只负责 HTTP

这是非常重要的一条。

Router：

```text
接收参数
 ↓
参数校验
 ↓
调用 Service
 ↓
返回结果
```

**不要在 Router 里面写业务逻辑。**

错误：

```python
@router.post("/chat")
async def chat(request):
    if request.temperature > 2:
        ...

    # 一大堆 AI 业务代码

    # 一大堆数据库代码

    # 一大堆判断
```

应该：

```python
@router.post("/chat")
async def chat(request: ChatRequest):
    return await chat_service.chat(request)
```

---

# 十九、Service 负责业务

例如：

```text
routers/chat.py
        ↓
services/chat_service.py
```

Router：

```python
@router.post("/chat")
async def chat(request: ChatRequest):
    return await service.chat(request)
```

Service：

```python
async def chat(request: ChatRequest):
    ...
```

这样以后你接真实的大模型：

```text
chat_service
      ↓
LLM Client
      ↓
DeepSeek / OpenAI / Qwen
```

非常自然。

---

# 二十、Schema 只负责数据结构

例如：

```python
class ChatRequest(BaseModel):
    message: str
    temperature: float
```

Schema 不负责：

```text
数据库操作
AI调用
日志
HTTP请求
```

它只负责：

> **“数据长什么样，以及数据是否合法。”**

---

# 二十一、import 规范

统一：

```python
import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services import chat_service
```

顺序：

```text
标准库
 ↓
第三方库
 ↓
项目内部模块
```

---

# 二十二、类型提示必须写

以后不要：

```python
def get_user(id):
```

而是：

```python
def get_user(user_id: int):
```

返回值也尽量写：

```python
async def get_user(user_id: int) -> User:
```

或者：

```python
async def get_user(user_id: int) -> UserResponse:
```

你以后进入 AI 后端开发，**类型提示一定要养成习惯。**

---

# 二十三、日志规范

禁止：

```python
print("用户创建成功")
```

统一：

```python
logger.info("用户创建成功")
```

异常：

```python
logger.exception("用户创建失败")
```

日志级别：

```text
DEBUG
INFO
WARNING
ERROR
EXCEPTION
```

一般：

```python
logger.info()
```

异常：

```python
logger.exception()
```

---

# 二十四、不要捕获所有异常

不要到处：

```python
try:
    ...
except Exception:
    return ...
```

尤其不要：

```python
except Exception:
    pass
```

项目统一异常交给：

```text
全局异常处理器
```

只有你确实知道如何处理某种异常时才捕获。

---

# 二十五、异步规范

以后看到：

```python
async def
```

里面需要异步等待，就使用：

```python
await
```

例如：

```python
await asyncio.sleep(1)
```

禁止在异步接口里面：

```python
time.sleep(1)
```

因为：

```text
time.sleep()
    ↓
阻塞 Event Loop
```

---

# 二十六、注释规范

不要写这种注释：

```python
# 定义用户
user = ...
```

这种注释没有意义。

应该解释：

> **为什么这么做。**

例如：

```python
# 使用 request_id 将一次请求的所有日志串联起来，
# 方便定位 AI 服务调用失败的问题。
request_id = str(uuid.uuid4())
```

---

# 二十七、API 命名规范

统一：

```text
/api/users
/api/users/{user_id}

/api/chat

/api/models
/api/models/{model_name}

/api/logs
```

不要：

```text
/api/getUser
/api/createUser
/api/deleteUser
```

因为 REST 风格通常使用：

```text
HTTP Method + Resource
```

表达操作。

例如：

```text
GET    /api/users
POST   /api/users
GET    /api/users/1
DELETE /api/users/1
```

---

# 二十八、你的最终挑战

这个项目不要一上来全部写完。

按照下面顺序写。

### 第 1 阶段

只实现：

```text
FastAPI
    ↓
GET /health
    ↓
JSONResponse
```

掌握：

```text
FastAPI
路由
Response
```

---

### 第 2 阶段

实现：

```text
users
```

掌握：

```text
Path 参数
Query 参数
Body 参数
Pydantic
```

---

### 第 3 阶段

实现：

```text
Depends
X-API-Key
```

掌握：

```text
依赖注入
```

---

### 第 4 阶段

实现：

```text
POST /api/chat
```

要求：

```python
async def
await asyncio.sleep()
```

掌握：

```text
异步接口
Coroutine
await
Event Loop
```

---

### 第 5 阶段

加入：

```text
Middleware
```

实现：

```text
request_id
请求日志
耗时
响应状态码
```

---

### 第 6 阶段

加入：

```text
全局异常处理
```

实现：

```text
400
401
404
500
```

---

### 第 7 阶段

最后再整理：

```text
routers
schemas
services
dependencies
middleware
exceptions
core
```

完成真正的项目结构。

---

# 二十九、最终你应该能讲清楚这一条链

当别人问你：

> “一个请求进入 FastAPI 后发生了什么？”

你应该能够自己回答：

```text
客户端
  ↓
HTTP Request
  ↓
Middleware
  ↓
Router
  ↓
Path / Query / Body 参数解析
  ↓
Pydantic 校验
  ↓
Depends 依赖注入
  ↓
Service
  ↓
业务逻辑
  ↓
async / await
  ↓
Response
  ↓
Middleware
  ↓
HTTP Response
  ↓
客户端
```

这就是这个练习项目真正的目的。

---

# 三十、最终验收标准

完成之后，你不能只满足：

> **“接口能访问。”**

而应该满足：

* [ ] 能解释 FastAPI 路由
* [ ] 能使用 Path 参数
* [ ] 能使用 Query 参数
* [ ] 能使用 Body 参数
* [ ] 能独立写 Pydantic Model
* [ ] 能使用 `Field`
* [ ] 能使用 `field_validator`
* [ ] 能使用 `model_validator`
* [ ] 能使用 Enum
* [ ] 能使用 `Depends`
* [ ] 能解释依赖注入
* [ ] 能写 `async def`
* [ ] 能正确使用 `await`
* [ ] 能解释为什么不能在 async 接口里使用 `time.sleep()`
* [ ] 能写 Middleware
* [ ] 能记录 request_id
* [ ] 能记录接口耗时
* [ ] 能写统一异常处理
* [ ] 能写统一响应
* [ ] 能使用 `logger` 而不是 `print`
* [ ] 能进行项目分层
* [ ] 能解释 Router / Schema / Service 各自负责什么
* [ ] 能用 Uvicorn 启动项目

## 最终目标

当这个项目完成后，你再开始真正的：

```text
ai-server
   ↓
LLM Client
   ↓
DeepSeek / Qwen / OpenAI
   ↓
Streaming
   ↓
RAG
   ↓
Embedding
   ↓
Vector DB
   ↓
Agent / Tool Calling
```

就不会变成“会调用一个大模型 API”，而是已经具备一个**真正 AI 后端服务的 FastAPI 骨架**。

