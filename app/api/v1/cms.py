"""业务模块说明。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.core.database import get_db
from app.models.cms_config import CMSConfig
from app.services.cms_service import CMSServiceFactory
from app.core.exceptions import CMSConnectionException

router = APIRouter()


class CMSConfigRequest(BaseModel):
    platform: str
    api_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: bool = True


class TestConnectionRequest(BaseModel):
    config_id: Optional[int] = None
    # 直接测试用（不保存配置时）
    platform: Optional[str] = None
    api_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


@router.post("/config")
async def create_cms_config(
    request: CMSConfigRequest,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    # 如果设置为激活，先取消其他配置的激活状态
    if request.is_active:
        db.query(CMSConfig).update({"is_active": False})
    
    # 检查是否已存在相同平台的配置
    existing = db.query(CMSConfig).filter(CMSConfig.platform == request.platform).first()
    
    if existing:
        # 更新
        existing.api_url = request.api_url
        existing.username = request.username
        existing.password = request.password
        existing.config = request.config
        existing.is_active = request.is_active
    else:
        # 创建
        existing = CMSConfig(
            platform=request.platform,
            api_url=request.api_url,
            username=request.username,
            password=request.password,
            config=request.config,
            is_active=request.is_active
        )
        db.add(existing)
    
    db.commit()
    db.refresh(existing)
    
    return {
        "success": True,
        "message": "配置保存成功",
        "data": {
            "id": existing.id,
            "platform": existing.platform,
            "api_url": existing.api_url,
            "is_active": existing.is_active
        }
    }


@router.get("/config")
async def get_cms_config_list(
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    configs = db.query(CMSConfig).all()
    return {
        "success": True,
        "data": [
            {
                "id": config.id,
                "platform": config.platform,
                "api_url": config.api_url,
                "username": config.username,
                "is_active": config.is_active,
                "created_at": config.created_at.isoformat() if config.created_at else None
            }
            for config in configs
        ]
    }


@router.get("/config/{config_id}")
async def get_cms_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    config = db.query(CMSConfig).filter(CMSConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="CMS配置不存在")
    
    return {
        "success": True,
        "data": {
            "id": config.id,
            "platform": config.platform,
            "api_url": config.api_url,
            "username": config.username,
            "password": config.password,
            "config": config.config,
            "is_active": config.is_active,
            "created_at": config.created_at.isoformat() if config.created_at else None
        }
    }


@router.delete("/config/{config_id}")
async def delete_cms_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    config = db.query(CMSConfig).filter(CMSConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="CMS配置不存在")
    
    db.delete(config)
    db.commit()
    
    return {"success": True, "message": "删除成功"}


@router.post("/test-connection")
async def test_connection(
    request: TestConnectionRequest,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    try:
        if request.config_id:
            # 使用已保存的配置测试
            success = CMSServiceFactory.test_connection(db, request.config_id)
        elif request.api_url and request.platform:
            # 使用直接提供的凭据测试（保存前测试）
            success = CMSServiceFactory.test_connection_direct(
                platform=request.platform,
                api_url=request.api_url,
                username=request.username,
                password=request.password
            )
        else:
            raise HTTPException(status_code=400, detail="请提供 config_id 或完整的连接信息")
        
        return {
            "success": True,
            "message": "连接测试成功"
        }
    except CMSConnectionException as e:
        raise HTTPException(status_code=400, detail=str(e))
