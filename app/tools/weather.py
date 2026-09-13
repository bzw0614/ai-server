"""

@Time :  
@Author : 4ever
@File : .py

"""
def get_weather(city: str):
    weather_data = {
        "北京": {
            "temperature": 25,
            "weather": "晴"
        },
        "上海": {
            "temperature": 28,
            "weather": "多云"
        },
        "烟台": {
            "temperature": 10000,
            "weather": "阴"
        }
    }

    return weather_data.get(city, {
        "temperature": None,
        "weather": "未知"
    })

'''
{
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": null,
                "tool_calls": [
                    {
                        "id": "call_001",
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "arguments": "{\"city\":\"北京\"}"
                        }
                    }
                ]
            }
        }
    ]
}
'''