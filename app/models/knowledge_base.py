"""业务模块说明。"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class KnowledgeBase(Base):
    """业务模块说明。"""
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_type = Column(String(10), nullable=False, comment="文件类型: txt/pdf")
    content = Column(Text, nullable=False, comment="文件内容")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, file_path={self.file_path})>"
