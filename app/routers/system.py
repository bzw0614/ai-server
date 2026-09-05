"""

@Time :  
@Author : 4ever
@File : .py

"""
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

system_router = APIRouter(tags=["system"])

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
@system_router.get("/health")
def health() -> JSONResponse:
    logger.info("检查健康状态")
    return JSONResponse(
        status_code=200,
        content={
            "message": "Healthy",
            "code": 0,
            "data":None
        }
    )
