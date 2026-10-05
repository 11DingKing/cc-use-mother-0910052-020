"""业务模块说明。"""
import logging
import requests
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.cms_config import CMSConfig
from app.core.exceptions import CMSConnectionException

logger = logging.getLogger(__name__)


class CMSService:
    """业务模块说明。"""
    
    def __init__(self, config: CMSConfig):
        self.config = config
    
    def test_connection(self) -> bool:
        """业务模块说明。"""
        raise NotImplementedError
    
    def publish_article(self, title: str, content: str) -> Dict[str, Any]:
        """业务模块说明。"""
        raise NotImplementedError


class WordPressService(CMSService):
    """业务模块说明。"""
    
    def _get_api_url(self, endpoint: str) -> str:
        """业务模块说明。"""
        base_url = self.config.api_url.rstrip('/')
        # 优先尝试 pretty permalink 格式，失败后使用 query string 格式
        return f"{base_url}/wp-json{endpoint}"
    
    def _get_fallback_url(self, endpoint: str) -> str:
        """业务模块说明。"""
        base_url = self.config.api_url.rstrip('/')
        return f"{base_url}/?rest_route={endpoint}"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """业务模块说明。"""
        auth = (self.config.username, self.config.password)
        kwargs['auth'] = auth
        kwargs['timeout'] = kwargs.get('timeout', 10)
        
        # 先尝试 pretty permalink 格式
        url = self._get_api_url(endpoint)
        try:
            response = getattr(requests, method)(url, **kwargs)
            # 如果返回HTML而不是JSON，尝试备用格式
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                url = self._get_fallback_url(endpoint)
                response = getattr(requests, method)(url, **kwargs)
            return response
        except requests.exceptions.SSLError:
            logger.warning("SSL验证失败，尝试跳过SSL验证")
            kwargs['verify'] = False
            response = getattr(requests, method)(url, **kwargs)
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                url = self._get_fallback_url(endpoint)
                response = getattr(requests, method)(url, **kwargs)
            return response
    
    def test_connection(self) -> bool:
        """业务模块说明。"""
        try:
            response = self._make_request('get', '/wp/v2/users/me')
            
            # 检查响应状态
            if response.status_code == 401:
                raise CMSConnectionException("认证失败，请检查用户名和应用密码")
            elif response.status_code == 403:
                raise CMSConnectionException("权限不足，请检查用户权限")
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', f'HTTP {response.status_code}')
                except:
                    error_msg = f"HTTP {response.status_code}"
                raise CMSConnectionException(f"连接失败: {error_msg}")
            
            response.raise_for_status()
            logger.info("WordPress连接测试成功")
            return True
        except CMSConnectionException:
            raise
        except requests.exceptions.SSLError as e:
            logger.error(f"WordPress SSL证书验证失败: {e}")
            raise CMSConnectionException(f"SSL证书验证失败，请检查网站证书配置")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"WordPress连接失败: {e}")
            raise CMSConnectionException(f"无法连接到WordPress站点，请检查地址是否正确")
        except requests.exceptions.Timeout:
            logger.error("WordPress连接超时")
            raise CMSConnectionException("连接超时，请检查网络或稍后重试")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise CMSConnectionException("认证失败，请检查用户名和应用密码")
            elif e.response.status_code == 403:
                raise CMSConnectionException("权限不足，请检查用户权限")
            elif e.response.status_code == 404:
                raise CMSConnectionException("API地址错误，请确认WordPress已启用REST API")
            else:
                raise CMSConnectionException(f"请求失败: HTTP {e.response.status_code}")
        except Exception as e:
            logger.error(f"WordPress连接测试失败: {e}")
            raise CMSConnectionException(f"连接失败: {str(e)}")
    
    def publish_article(self, title: str, content: str) -> Dict[str, Any]:
        """业务模块说明。"""
        try:
            data = {
                "title": title,
                "content": content,
                "status": "publish"  # 直接发布
            }
            
            logger.info(f"发布文章到WordPress")
            
            response = self._make_request('post', '/wp/v2/posts', json=data, timeout=30)
            
            # 检查响应状态
            if response.status_code == 401:
                raise CMSConnectionException("认证失败，请检查用户名和应用密码")
            elif response.status_code == 403:
                raise CMSConnectionException("权限不足，请检查用户是否有发布权限")
            elif response.status_code >= 400:
                # 尝试获取错误信息
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', f'HTTP {response.status_code}')
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                raise CMSConnectionException(f"发布失败: {error_msg}")
            
            # 解析响应
            try:
                result = response.json()
            except Exception as e:
                logger.error(f"响应解析失败，状态码: {response.status_code}, 内容: {response.text[:500]}")
                raise CMSConnectionException(f"WordPress返回无效响应，请检查API配置")
            
            logger.info(f"文章发布成功: {result.get('id')}")
            
            return {
                "success": True,
                "post_id": result.get("id"),
                "link": result.get("link"),
                "message": "发布成功"
            }
        except CMSConnectionException:
            raise
        except requests.exceptions.SSLError:
            error_msg = "SSL证书验证失败，请检查网站证书配置"
            logger.error(error_msg)
            raise CMSConnectionException(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"无法连接到WordPress: {str(e)}"
            logger.error(error_msg)
            raise CMSConnectionException(error_msg)
        except Exception as e:
            error_msg = f"WordPress发布失败: {str(e)}"
            logger.error(error_msg)
            raise CMSConnectionException(error_msg)


class CMSServiceFactory:
    """业务模块说明。"""
    
    @staticmethod
    def create_service(config: CMSConfig) -> CMSService:
        """业务模块说明。"""
        platform = config.platform.lower()
        
        if platform == "wordpress":
            return WordPressService(config)
        else:
            raise CMSConnectionException(f"不支持的CMS平台: {platform}")
    
    @staticmethod
    def get_active_config(db: Session) -> Optional[CMSConfig]:
        """业务模块说明。"""
        return db.query(CMSConfig).filter(CMSConfig.is_active == True).first()
    
    @staticmethod
    def test_connection(db: Session, config_id: int) -> bool:
        """业务模块说明。"""
        config = db.query(CMSConfig).filter(CMSConfig.id == config_id).first()
        if not config:
            raise CMSConnectionException("CMS配置不存在")
        
        service = CMSServiceFactory.create_service(config)
        return service.test_connection()
    
    @staticmethod
    def test_connection_direct(platform: str, api_url: str, username: str = None, password: str = None) -> bool:
        """业务模块说明。"""
        # 创建临时配置对象
        temp_config = CMSConfig(
            platform=platform,
            api_url=api_url,
            username=username,
            password=password
        )
        
        service = CMSServiceFactory.create_service(temp_config)
        return service.test_connection()
    
    @staticmethod
    def publish_article(db: Session, article_id: int, title: str, content: str) -> Dict[str, Any]:
        """业务模块说明。"""
        from app.models.article import Article
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise CMSConnectionException("文章不存在")
        
        if not article.cms_config_id:
            # 使用激活的配置
            config = CMSServiceFactory.get_active_config(db)
            if not config:
                raise CMSConnectionException("未配置CMS")
        else:
            config = db.query(CMSConfig).filter(CMSConfig.id == article.cms_config_id).first()
            if not config:
                raise CMSConnectionException("CMS配置不存在")
        
        service = CMSServiceFactory.create_service(config)
        return service.publish_article(title, content)
