"""业务模块说明。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database_async import init_async_db
from app.core.exceptions import (
    global_exception_handler,
    app_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    AppException
)
from app.api.v1 import router as api_router
from app.core.scheduler import scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """业务模块说明。"""
    setup_logging(mode="api")
    testing = bool(app.dependency_overrides)

    if not testing:
        logger.info("正在初始化数据库...")
        await init_async_db()
        logger.info("数据库初始化完成")

        if not scheduler.running:
            logger.info("正在启动调度器...")
            scheduler.start()
            logger.info("调度器启动完成")

    try:
        yield
    finally:
        if not testing and scheduler.running:
            logger.info("正在关闭调度器...")
            scheduler.shutdown(wait=False)
            logger.info("调度器已关闭")


app = FastAPI(
    title="AI文章自动生成与发布系统",
    description="基于DeepSeek API的自动文章生成与CMS发布系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """业务模块说明。"""
    return {"status": "ok", "message": "AI文章自动生成与发布系统运行中"}


@app.get("/health")
async def health():
    """业务模块说明。"""
    return {"status": "healthy"}
