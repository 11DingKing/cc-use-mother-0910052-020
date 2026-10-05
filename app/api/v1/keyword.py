"""业务模块说明。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.services.keyword_service import KeywordService

router = APIRouter()


class CreateKeywordsRequest(BaseModel):
    keywords: List[str]


class UpdateKeywordRequest(BaseModel):
    keyword: str


@router.post("")
async def create_keywords(
    request: CreateKeywordsRequest,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    result = KeywordService.create(db, request.keywords)
    return {
        "success": True,
        "message": "关键词添加完成",
        "data": result
    }


@router.get("")
async def get_keyword_list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    keywords = KeywordService.get_list(db, skip, limit)
    return {
        "success": True,
        "data": [
            {
                "id": kw.id,
                "keyword": kw.keyword,
                "created_at": kw.created_at.isoformat() if kw.created_at else None
            }
            for kw in keywords
        ]
    }


@router.get("/{keyword_id}")
async def get_keyword(
    keyword_id: int,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    keyword = KeywordService.get_by_id(db, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    return {
        "success": True,
        "data": {
            "id": keyword.id,
            "keyword": keyword.keyword,
            "created_at": keyword.created_at.isoformat() if keyword.created_at else None
        }
    }


@router.put("/{keyword_id}")
async def update_keyword(
    keyword_id: int,
    request: UpdateKeywordRequest,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    keyword = KeywordService.update(db, keyword_id, request.keyword)
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    return {
        "success": True,
        "message": "更新成功",
        "data": {
            "id": keyword.id,
            "keyword": keyword.keyword
        }
    }


@router.delete("/{keyword_id}")
async def delete_keyword(
    keyword_id: int,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    success = KeywordService.delete(db, keyword_id)
    if not success:
        raise HTTPException(status_code=404, detail="关键词不存在")
    
    return {"success": True, "message": "删除成功"}
