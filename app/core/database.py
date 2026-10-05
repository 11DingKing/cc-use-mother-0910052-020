"""业务模块说明。"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base

# 确保数据目录存在
os.makedirs(os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    """业务模块说明。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """业务模块说明。"""
    from app.models import (
        KnowledgeBase, Keyword, CMSConfig, Article, 
        PublishLog, SystemConfig
    )
    from app.models.user import User
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 初始化默认用户
        from app.services.auth_service import init_default_user
        init_default_user(db)
        
        # 初始化默认配置
        _init_default_config(db)
    finally:
        db.close()


def _init_default_config(db):
    """业务模块说明。"""
    from app.models.system_config import SystemConfig
    from app.models.cms_config import CMSConfig
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 初始化系统配置
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
    
    # 初始化 CMS 配置
    existing_cms = db.query(CMSConfig).filter(CMSConfig.id == 1).first()
    if not existing_cms:
        # 统一使用 localhost:8082，Docker 环境通过 extra_hosts 映射
        cms_config = CMSConfig(
            platform="wordpress",
            api_url="http://localhost:8082",
            username="admin",
            password="",  # Docker 环境由 wordpress-init 写入，本地需运行脚本
            is_active=True
        )
        db.add(cms_config)
        logger.info("初始化 CMS 配置: WordPress (http://localhost:8082)")
    
    db.commit()
