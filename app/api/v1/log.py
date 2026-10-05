"""业务模块说明。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.publish_log import PublishLog

router = APIRouter()


@router.get("")
async def get_log_list(
    skip: int = 0,
    limit: int = 100,
    article_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    query = db.query(PublishLog)
    if article_id:
        query = query.filter(PublishLog.article_id == article_id)
    
    logs = query.order_by(PublishLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": log.id,
                "article_id": log.article_id,
                "status": log.status,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    }


@router.get("/{log_id}")
async def get_log(
    log_id: int,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    log = db.query(PublishLog).filter(PublishLog.id == log_id).first()
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="日志不存在")
    
    return {
        "success": True,
        "data": {
            "id": log.id,
            "article_id": log.article_id,
            "status": log.status,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
    }
