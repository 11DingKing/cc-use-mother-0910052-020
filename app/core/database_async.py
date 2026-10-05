"""业务模块说明。"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.models.base import Base

os.makedirs(os.path.dirname(settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")), exist_ok=True)


def get_async_database_url() -> str:
    """业务模块说明。"""
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    return url


engine_options = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
    "connect_args": {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
}
if "sqlite" not in settings.DATABASE_URL:
    engine_options.update(
        pool_size=settings.API_POOL_SIZE,
        max_overflow=settings.API_MAX_OVERFLOW,
    )

async_engine = create_async_engine(get_async_database_url(), **engine_options)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_async_db():
    """业务模块说明。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_async_db():
    """业务模块说明。"""
    from app.models import (
        KnowledgeBase, Keyword, CMSConfig, Article, 
        PublishLog, SystemConfig
    )
    from app.models.user import User
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    from app.core.database_sync import SyncSessionLocal
    from app.services.auth_service import init_default_user
    
    def sync_init():
        sync_db = SyncSessionLocal()
        try:
            init_default_user(sync_db)
            _init_default_config_sync(sync_db)
        finally:
            sync_db.close()
    
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, sync_init)


def _init_default_config_sync(db):
    """业务模块说明。"""
    from app.models.system_config import SystemConfig
    from app.models.cms_config import CMSConfig
    import logging
    
    logger = logging.getLogger(__name__)
    
    default_configs = {
        "generation_count": "3",
        "frequency_unit": "hour",
        "frequency_value": "1",
        "deepseek_api_key": "",
        "deepseek_api_url": "https://api.deepseek.com/v1/chat/completions",
        "deepseek_timeout": "60"
    }
    
    for key, value in default_configs.items():
        existing = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        if not existing:
            config = SystemConfig(config_key=key, config_value=value)
            db.add(config)
            logger.info(f"初始化系统配置: {key}")
    
    existing_cms = db.query(CMSConfig).filter(CMSConfig.id == 1).first()
    if not existing_cms:
        cms_config = CMSConfig(
            platform="wordpress",
            api_url="http://localhost:8082",
            username="admin",
            password="",
            is_active=True
        )
        db.add(cms_config)
        logger.info("初始化 CMS 配置: WordPress (http://localhost:8082)")
    
    db.commit()
