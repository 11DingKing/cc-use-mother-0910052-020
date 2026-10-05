"""业务模块说明。"""
from fastapi import APIRouter
from app.api.v1 import (
    knowledge_base,
    keyword,
    cms,
    article,
    config,
    log,
    auth
)

router = APIRouter()

router.include_router(auth.router)
router.include_router(knowledge_base.router, prefix="/knowledge-base", tags=["知识库管理"])
router.include_router(keyword.router, prefix="/keywords", tags=["关键词管理"])
router.include_router(cms.router, prefix="/cms", tags=["CMS管理"])
router.include_router(article.router, prefix="/articles", tags=["文章管理"])
router.include_router(config.router, prefix="/config", tags=["系统配置"])
router.include_router(log.router, prefix="/logs", tags=["日志管理"])
