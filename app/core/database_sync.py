"""业务模块说明。"""
import os
from contextlib import contextmanager
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.models.base import Base

os.makedirs(os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)

sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.GUI_POOL_SIZE,
    max_overflow=settings.GUI_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)


def get_sync_db():
    """业务模块说明。"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_sync_db_context():
    """业务模块说明。"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_db_connection() -> bool:
    """业务模块说明。"""
    try:
        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        return True
    except OperationalError:
        return False
    except Exception:
        return False


def init_sync_db():
    """业务模块说明。"""
    from app.models import (
        KnowledgeBase, Keyword, CMSConfig, Article, 
        PublishLog, SystemConfig
    )
    from app.models.user import User
    
    Base.metadata.create_all(bind=sync_engine)
    
    db = SyncSessionLocal()
    try:
        from app.services.auth_service import init_default_user
        init_default_user(db)
        _init_default_config(db)
    finally:
        db.close()


def _init_default_config(db):
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
