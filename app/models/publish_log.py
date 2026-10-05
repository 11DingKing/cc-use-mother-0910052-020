"""业务模块说明。"""
from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class PublishLog(Base):
    """业务模块说明。"""
    __tablename__ = "publish_log"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("article.id"), nullable=False, comment="文章ID")
    status = Column(String(20), nullable=False, comment="状态: success/failed")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<PublishLog(id={self.id}, article_id={self.article_id}, status={self.status})>"
