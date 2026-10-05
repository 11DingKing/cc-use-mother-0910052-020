"""业务模块说明。"""
import logging
from typing import Optional, Dict, Any

from app.models.cms_config import CMSConfig
from app.core.exceptions import CMSConnectionException
from app.services.cms_service import CMSServiceFactory

logger = logging.getLogger(__name__)


class CMSBusinessLogic:
    """业务模块说明。"""
    
    @staticmethod
    def get_active_config(db) -> Optional[CMSConfig]:
        """业务模块说明。"""
        return db.query(CMSConfig).filter(CMSConfig.is_active == True).first()
    
    @staticmethod
    def get_config(db, config_id: int) -> Optional[CMSConfig]:
        """业务模块说明。"""
        return db.query(CMSConfig).filter(CMSConfig.id == config_id).first()
    
    @staticmethod
    def get_all_configs(db) -> list:
        """业务模块说明。"""
        return db.query(CMSConfig).all()
    
    @staticmethod
    def create_config(
        db,
        platform: str,
        api_url: str,
        username: str,
        password: str,
        is_active: bool = False
    ) -> CMSConfig:
        """业务模块说明。"""
        if is_active:
            db.query(CMSConfig).update({"is_active": False})
        
        config = CMSConfig(
            platform=platform,
            api_url=api_url,
            username=username,
            password=password,
            is_active=is_active
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        
        logger.info(f"已创建CMS配置: {platform} - {api_url}")
        return config
    
    @staticmethod
    def update_config(
        db,
        config_id: int,
        platform: str = None,
        api_url: str = None,
        username: str = None,
        password: str = None,
        is_active: bool = None
    ) -> Optional[CMSConfig]:
        """业务模块说明。"""
        config = db.query(CMSConfig).filter(CMSConfig.id == config_id).first()
        if not config:
            return None
        
        if is_active is not None and is_active:
            db.query(CMSConfig).update({"is_active": False})
        
        if platform is not None:
            config.platform = platform
        if api_url is not None:
            config.api_url = api_url
        if username is not None:
            config.username = username
        if password is not None:
            config.password = password
        if is_active is not None:
            config.is_active = is_active
        
        db.commit()
        db.refresh(config)
        
        logger.info(f"已更新CMS配置: {config_id}")
        return config
    
    @staticmethod
    def delete_config(db, config_id: int) -> bool:
        """业务模块说明。"""
        config = db.query(CMSConfig).filter(CMSConfig.id == config_id).first()
        if config:
            db.delete(config)
            db.commit()
            logger.info(f"已删除CMS配置: {config_id}")
            return True
        return False
    
    @staticmethod
    def test_connection(db, config_id: int) -> bool:
        """业务模块说明。"""
        config = db.query(CMSConfig).filter(CMSConfig.id == config_id).first()
        if not config:
            raise CMSConnectionException("CMS配置不存在")
        
        service = CMSServiceFactory.create_service(config)
        return service.test_connection()
    
    @staticmethod
    def test_connection_direct(
        platform: str,
        api_url: str,
        username: str = None,
        password: str = None
    ) -> bool:
        """业务模块说明。"""
        temp_config = CMSConfig(
            platform=platform,
            api_url=api_url,
            username=username,
            password=password
        )
        
        service = CMSServiceFactory.create_service(temp_config)
        return service.test_connection()
