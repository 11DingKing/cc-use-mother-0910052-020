"""业务模块说明。"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class CMSConfig(Base):
    """业务模块说明。"""
    __tablename__ = "cms_config"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False, comment="CMS平台: wordpress/其他")
    api_url = Column(String(500), nullable=False, comment="API地址")
    username = Column(String(100), comment="用户名")
    password = Column(String(500), comment="密码/认证令牌")
    config = Column(JSON, comment="额外配置信息")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<CMSConfig(id={self.id}, platform={self.platform})>"
