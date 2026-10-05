"""业务模块说明。"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.keyword import Keyword

logger = logging.getLogger(__name__)


class KeywordService:
    """业务模块说明。"""
    
    @staticmethod
    def create(db: Session, keywords: List[str]) -> dict:
        """业务模块说明。"""
        created = 0
        skipped = 0
        errors = []
        
        for keyword in keywords:
            keyword = keyword.strip()
            if not keyword:
                continue
            
            try:
                # 检查是否已存在
                existing = db.query(Keyword).filter(
                    Keyword.keyword == keyword
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                kw = Keyword(keyword=keyword)
                db.add(kw)
                created += 1
                logger.info(f"已添加关键词: {keyword}")
            except IntegrityError:
                db.rollback()
                skipped += 1
            except Exception as e:
                error_msg = f"添加关键词失败 {keyword}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        db.commit()
        
        return {
            "created": created,
            "skipped": skipped,
            "errors": errors
        }
    
    @staticmethod
    def get_list(db: Session, skip: int = 0, limit: int = 100) -> List[Keyword]:
        """业务模块说明。"""
        return db.query(Keyword).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, keyword_id: int) -> Optional[Keyword]:
        """业务模块说明。"""
        return db.query(Keyword).filter(Keyword.id == keyword_id).first()
    
    @staticmethod
    def delete(db: Session, keyword_id: int) -> bool:
        """业务模块说明。"""
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword:
            db.delete(keyword)
            db.commit()
            logger.info(f"已删除关键词: {keyword_id}")
            return True
        return False
    
    @staticmethod
    def update(db: Session, keyword_id: int, new_keyword: str) -> Optional[Keyword]:
        """业务模块说明。"""
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword:
            keyword.keyword = new_keyword.strip()
            db.commit()
            logger.info(f"已更新关键词: {keyword_id}")
            return keyword
        return None
    
    @staticmethod
    def get_all_keywords(db: Session) -> List[str]:
        """业务模块说明。"""
        keywords = db.query(Keyword).all()
        return [kw.keyword for kw in keywords]
