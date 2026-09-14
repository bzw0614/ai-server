"""

@Time :  
@Author : 4ever
@File : .py

"""

# OpenAI 风格的标准 Tool Calling API
WEATHER_TOOL = {
# 告诉llm这是一个函数工具
    "type": "function",
# 函数工具内容：
    "function": {
        # 工具名字 让llm知道调用你的函数获取数据
        "name": "get_weather",
        # 帮助 LLM 判断：用户的问题是不是应该使用这个工具？
        "description": "查询指定城市的天气",
        # 函数参数 在告诉 LLM：这个函数需要什么参数，以及参数是什么类型
        "parameters": {
            # object告诉 LLM：这个参数整体是一个“对象”，里面包含一个或多个字段。
            # 告诉 LLM：
            # “这个函数接收的参数不是一个单独的值，而是一组键值对组成的对象。”
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，例如北京、上海、烟台"
                }
            },
            # 规定 city 是必须提供的参数。
            "required": ["city"]
        }
    }
}

DATABASE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_user_by_name",
        # 描述是模型判断「该不该用这个工具、怎么用」的唯一依据：
        # 要写明支持模糊匹配、返回的是列表，否则「名字里带 b 的用户有哪些」
        # 这种列举型问题会被模型判为不适用，直接凭常识乱答。
        "description": (
            "按用户名模糊查询用户，返回所有名字中包含该关键字的用户列表"
            "（含 id、name、age、email）。"
            "当用户问「有哪些用户」「名字里带 xx 的人是谁」这类列举问题时使用本工具。"
        ),
        # required 必须放在 parameters 内部、和 properties 同级。
        # 放到 function 这一层不是合法字段，会被上游忽略，等于没声明必填项。
        "parameters": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "用户名关键字，支持模糊匹配，例如 b、zhang、张三"
                }
            },
            "required": ["username"]
        }
    }
}
