"""业务模块说明。"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """业务模块说明。"""
    
    # DeepSeek API配置（默认值，可被数据库配置覆盖）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_TIMEOUT: int = 60
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/app.db"
    
    # GUI数据库连接池配置
    GUI_POOL_SIZE: int = 3
    GUI_MAX_OVERFLOW: int = 2
    
    # API数据库连接池配置
    API_POOL_SIZE: int = 10
    API_MAX_OVERFLOW: int = 5
    
    # 应用配置
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = False
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_BACKUP_DAYS: int = 7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def get_deepseek_config_from_db():
    """业务模块说明。"""
    from app.core.database import SessionLocal
    from app.models.system_config import SystemConfig
    
    db = SessionLocal()
    try:
        api_key = db.query(SystemConfig).filter(SystemConfig.config_key == "deepseek_api_key").first()
        api_url = db.query(SystemConfig).filter(SystemConfig.config_key == "deepseek_api_url").first()
        timeout = db.query(SystemConfig).filter(SystemConfig.config_key == "deepseek_timeout").first()
        
        return {
            "api_key": api_key.config_value if api_key else settings.DEEPSEEK_API_KEY,
            "api_url": api_url.config_value if api_url else settings.DEEPSEEK_API_URL,
            "timeout": int(timeout.config_value) if timeout else settings.DEEPSEEK_TIMEOUT
        }
    finally:
        db.close()
