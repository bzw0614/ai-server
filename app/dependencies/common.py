"""

@Time :  
@Author : 4ever
@File : .py

"""
from fastapi import Header, HTTPException
from app.exceptions.handlers import ValidationError
# 校验x-api-key
API_KEY = "test-key"
'''
Header(...): 告诉 FastAPI：这个参数不要从 JSON 请求体里找，而是从 HTTP 请求头（Header）里找。
1. 参数...代表 必须提供
2. 参数None代表 可以不提供
3. 参数abc代表 默认值是 "abc"
'''
def validate_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key 无效")