"""业务模块说明。"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Article(Base):
    """业务模块说明。"""
    __tablename__ = "article"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, comment="文章标题")
    content = Column(Text, nullable=False, comment="文章内容")
    cms_config_id = Column(Integer, ForeignKey("cms_config.id"), nullable=True, comment="CMS配置ID")
    status = Column(String(20), default="pending", comment="状态: pending/published/failed")
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), comment="生成时间")
    published_at = Column(DateTime(timezone=True), nullable=True, comment="发布时间")
    
    # 关系
    cms_config = relationship("CMSConfig", backref="articles")
    
    def __repr__(self):
        return f"<Article(id={self.id}, title={self.title[:50]})>"
