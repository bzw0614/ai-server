"""

@Time :  
@Author : 4ever
@File : .py

"""

from fastapi.responses import JSONResponse
# 成功响应
def ok(data = None,message = "success",status = 200) -> JSONResponse:
    return JSONResponse(
        status_code = status,
        content = {
            "message": message,
            "data": data,
            "code": 0
        }
    )
# 错误响应
def error(message,status) -> JSONResponse:
    return JSONResponse(
        status_code = status,
        content = {
            "message": message,
            "code": status,
            "data": None
        }
    )