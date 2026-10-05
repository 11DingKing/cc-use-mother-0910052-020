"""业务模块说明。"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class Keyword(Base):
    """业务模块说明。"""
    __tablename__ = "keyword"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), nullable=False, unique=True, comment="关键词")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<Keyword(id={self.id}, keyword={self.keyword})>"
