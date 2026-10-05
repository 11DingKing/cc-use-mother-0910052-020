"""业务模块说明。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.config import settings, get_deepseek_config_from_db
from app.models.system_config import SystemConfig

router = APIRouter()


class DeepSeekConfigRequest(BaseModel):
    api_key: str
    api_url: Optional[str] = None
    model: Optional[str] = None
    timeout: Optional[int] = None


@router.get("/deepseek")
async def get_deepseek_config(db: Session = Depends(get_db)):
    """业务模块说明。"""
    try:
        config = get_deepseek_config_from_db()
        # 获取 model 配置
        model_config = db.query(SystemConfig).filter(SystemConfig.config_key == "deepseek_model").first()
        model = model_config.config_value if model_config else "deepseek-chat"
        
        # 隐藏API密钥的大部分内容
        masked_key = ""
        if config["api_key"] and len(config["api_key"]) > 10:
            masked_key = config["api_key"][:8] + "*" * 20 + config["api_key"][-4:]
        return {
            "success": True,
            "data": {
                "api_key_masked": masked_key,
                "has_api_key": bool(config["api_key"]),
                "api_url": config["api_url"],
                "model": model,
                "timeout": config["timeout"]
            }
        }
    except Exception:
        return {
            "success": True,
            "data": {
                "api_key_masked": "",
                "has_api_key": False,
                "api_url": settings.DEEPSEEK_API_URL,
                "model": "deepseek-chat",
                "timeout": settings.DEEPSEEK_TIMEOUT
            }
        }


@router.put("/deepseek")
async def update_deepseek_config(
    request: DeepSeekConfigRequest,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    def set_config(key: str, value: str):
        config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        if config:
            config.config_value = value
        else:
            config = SystemConfig(config_key=key, config_value=value)
            db.add(config)
    
    # 只有当用户输入了新的API密钥时才更新
    if request.api_key and not request.api_key.startswith("*"):
        set_config("deepseek_api_key", request.api_key)
    
    if request.api_url:
        set_config("deepseek_api_url", request.api_url)
    if request.model:
        set_config("deepseek_model", request.model)
    if request.timeout:
        set_config("deepseek_timeout", str(request.timeout))
    
    db.commit()
    
    return {
        "success": True,
        "message": "配置更新成功"
    }
