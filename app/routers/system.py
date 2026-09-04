"""

@Time :  
@Author : 4ever
@File : .py

"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

system_router = APIRouter()


@system_router.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "message": "Healthy",
            "code": 0,
            "data":None
        }
    )
