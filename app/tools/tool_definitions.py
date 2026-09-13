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
