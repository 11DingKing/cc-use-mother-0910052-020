"""业务模块说明。"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class AppException(Exception):
    """业务模块说明。"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class APIException(AppException):
    """业务模块说明。"""
    pass


class FileReadException(AppException):
    """业务模块说明。"""
    pass


class DeepSeekAPIException(AppException):
    """业务模块说明。"""
    pass


class CMSConnectionException(AppException):
    """业务模块说明。"""
    pass


async def global_exception_handler(request: Request, exc: Exception):
    """业务模块说明。"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服务器内部错误",
            "detail": str(exc)
        }
    )


async def app_exception_handler(request: Request, exc: AppException):
    """业务模块说明。"""
    logger.error(f"应用异常: {exc.message}")
    return JSONResponse(
        status_code=exc.code,
        content={
            "success": False,
            "message": exc.message
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """业务模块说明。"""
    logger.warning(f"参数验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "参数验证失败",
            "detail": exc.errors()
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """业务模块说明。"""
    logger.error(f"数据库异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "数据库操作失败",
            "detail": str(exc)
        }
    )
