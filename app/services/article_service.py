"""业务模块说明。"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.publish_log import PublishLog
from app.models.system_config import SystemConfig
from app.services.keyword_service import KeywordService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.deepseek_service import DeepSeekService
from app.services.cms_service import CMSServiceFactory
from app.core.exceptions import APIException
from app.core.scheduler import start_scheduled_publish, stop_scheduled_publish, get_scheduled_publish_status

logger = logging.getLogger(__name__)


class ArticleService:
    """业务模块说明。"""
    
    @staticmethod
    def generate_articles(
        db: Session,
        count: int,
        keyword_ids: Optional[List[int]] = None,
        use_knowledge_base: bool = True,
        mock: bool = False
    ) -> dict:
        """业务模块说明。"""
        # 验证触发条件：至少需要关键词或知识库
        from app.models.keyword import Keyword
        keywords = []
        if keyword_ids:
            keywords = [kw.keyword for kw_id in keyword_ids 
                       for kw in [db.query(Keyword).filter(Keyword.id == kw_id).first()] if kw]
        
        all_keywords = KeywordService.get_all_keywords(db) if not keywords else keywords
        
        # Mock 模式不需要加载知识库内容
        knowledge_base_content = ""
        if use_knowledge_base and not mock:
            knowledge_base_content = KnowledgeBaseService.get_all_content(db)
        
        if not all_keywords and not knowledge_base_content:
            raise APIException("至少需要指定关键词或知识库中的一项才能生成文章", code=400)
        
        generated = []
        errors = []
        
        # 获取已存在的标题，避免生成重复标题
        existing_titles = [a.title for a in db.query(Article.title).all()]
        
        for i in range(count):
            try:
                logger.info(f"开始生成第 {i+1}/{count} 篇文章")
                
                if mock:
                    # 模拟生成
                    import random
                    kw = random.choice(all_keywords) if all_keywords else "测试"
                    title = f"【{kw}】深度解析：{kw}的核心要点与实践指南"
                    content = f"""<h2>引言</h2>
<p>在当今快速发展的时代，{kw}已经成为各行各业关注的焦点。本文将从多个角度深入分析{kw}的核心概念、应用场景及未来发展趋势。</p>

<h2>什么是{kw}？</h2>
<p>{kw}是指在特定领域中，通过系统化的方法和工具，实现目标优化和效率提升的过程。它涵盖了理论研究、实践应用和持续改进等多个方面。</p>

<h2>{kw}的核心要素</h2>
<p>要深入理解{kw}，我们需要关注以下几个核心要素：</p>
<p>1. <strong>基础理论</strong>：掌握{kw}的基本原理和方法论</p>
<p>2. <strong>实践技能</strong>：将理论知识转化为实际操作能力</p>
<p>3. <strong>持续学习</strong>：跟踪{kw}领域的最新发展动态</p>

<h2>实践建议</h2>
<p>对于希望在{kw}领域取得突破的从业者，建议从以下几个方面入手：</p>
<p>首先，建立扎实的理论基础；其次，通过项目实践积累经验；最后，保持开放的学习心态。</p>

<h2>总结</h2>
<p>{kw}作为一个重要的研究和应用领域，具有广阔的发展前景。希望本文能够为读者提供有价值的参考和启发。</p>"""
                else:
                    # 调用 DeepSeek API 生成
                    title = DeepSeekService.generate_title(
                        keywords=all_keywords,
                        knowledge_base_content=knowledge_base_content,
                        existing_titles=existing_titles
                    )
                    # 将新标题加入已存在列表，避免后续重复
                    existing_titles.append(title)
                    
                    content = DeepSeekService.generate_content(
                        title=title,
                        keywords=all_keywords,
                        knowledge_base_content=knowledge_base_content
                    )
                
                # 保存文章
                article = Article(
                    title=title,
                    content=content,
                    status="pending"
                )
                db.add(article)
                db.commit()
                db.refresh(article)
                
                generated.append({
                    "id": article.id,
                    "title": title
                })
                
                logger.info(f"文章生成成功: {article.id} - {title[:50]}")
                
            except Exception as e:
                error_msg = f"生成第 {i+1} 篇文章失败: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
        
        return {
            "generated": len(generated),
            "articles": generated,
            "errors": errors
        }
    
    @staticmethod
    def get_list(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> dict:
        """业务模块说明。"""
        query = db.query(Article)
        if status:
            query = query.filter(Article.status == status)
        
        total = query.count()
        items = query.order_by(Article.generated_at.desc()).offset(skip).limit(limit).all()
        
        return {"items": items, "total": total}
    
    @staticmethod
    def get_stats(db: Session) -> dict:
        """业务模块说明。"""
        total = db.query(Article).count()
        pending = db.query(Article).filter(Article.status == "pending").count()
        published = db.query(Article).filter(Article.status == "published").count()
        failed = db.query(Article).filter(Article.status == "failed").count()
        return {"total": total, "pending": pending, "published": published, "failed": failed}
    
    @staticmethod
    def get_by_id(db: Session, article_id: int) -> Optional[Article]:
        """业务模块说明。"""
        return db.query(Article).filter(Article.id == article_id).first()
    
    @staticmethod
    def publish_article(db: Session, article_id: int) -> dict:
        """业务模块说明。"""
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise APIException("文章不存在", code=404)
        
        if article.status == "published":
            return {"success": True, "message": "文章已发布"}
        
        try:
            result = CMSServiceFactory.publish_article(
                db, article_id, article.title, article.content
            )
            
            if result["success"]:
                article.status = "published"
                article.published_at = datetime.now()
                db.commit()
                
                # 记录发布日志
                log = PublishLog(
                    article_id=article_id,
                    status="success"
                )
                db.add(log)
                db.commit()
                
                logger.info(f"文章发布成功: {article_id}")
                return {"success": True, "message": "发布成功", **result}
            else:
                raise Exception(result.get("message", "发布失败"))
                
        except Exception as e:
            article.status = "failed"
            db.commit()
            
            # 记录失败日志
            log = PublishLog(
                article_id=article_id,
                status="failed",
                error_message=str(e)
            )
            db.add(log)
            db.commit()
            
            logger.error(f"文章发布失败: {article_id} - {e}")
            raise APIException(f"发布失败: {str(e)}", code=500)
    
    @staticmethod
    def publish_all(db: Session) -> dict:
        """业务模块说明。"""
        pending_articles = db.query(Article).filter(Article.status == "pending").all()
        
        if not pending_articles:
            return {"success": True, "message": "没有待发布的文章", "published": 0, "failed": 0}
        
        published = 0
        failed = 0
        errors = []
        
        for article in pending_articles:
            try:
                ArticleService.publish_article(db, article.id)
                published += 1
            except Exception as e:
                failed += 1
                errors.append(f"文章 {article.id} 发布失败: {str(e)}")
        
        return {
            "success": True,
            "published": published,
            "failed": failed,
            "errors": errors
        }
    
    @staticmethod
    def get_generation_config(db: Session) -> dict:
        """业务模块说明。"""
        count = db.query(SystemConfig).filter(SystemConfig.config_key == "generation_count").first()
        publish_count = db.query(SystemConfig).filter(SystemConfig.config_key == "publish_count").first()
        frequency_unit = db.query(SystemConfig).filter(SystemConfig.config_key == "frequency_unit").first()
        frequency_value = db.query(SystemConfig).filter(SystemConfig.config_key == "frequency_value").first()
        
        return {
            "count": int(count.config_value) if count else 1,
            "publish_count": int(publish_count.config_value) if publish_count else 1,
            "frequency_unit": frequency_unit.config_value if frequency_unit else "hour",
            "frequency_value": int(frequency_value.config_value) if frequency_value else 1
        }
    
    @staticmethod
    def update_generation_config(
        db: Session,
        count: int,
        publish_count: int,
        frequency_unit: str,
        frequency_value: int
    ):
        """业务模块说明。"""
        def set_config(key: str, value: str):
            config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
            if config:
                config.config_value = value
            else:
                config = SystemConfig(config_key=key, config_value=value)
                db.add(config)
        
        set_config("generation_count", str(count))
        set_config("publish_count", str(publish_count))
        set_config("frequency_unit", frequency_unit)
        set_config("frequency_value", str(frequency_value))
        
        db.commit()
        logger.info(f"已更新生成配置: count={count}, publish_count={publish_count}, frequency={frequency_value}{frequency_unit}")
    
    @staticmethod
    def delete_article(db: Session, article_id: int) -> bool:
        """业务模块说明。"""
        article = db.query(Article).filter(Article.id == article_id).first()
        if article:
            # 同时删除相关的发布日志
            db.query(PublishLog).filter(PublishLog.article_id == article_id).delete()
            db.delete(article)
            db.commit()
            logger.info(f"已删除文章: {article_id}")
            return True
        return False
    
    @staticmethod
    def update_article(db: Session, article_id: int, title: str, content: str) -> Optional[Article]:
        """业务模块说明。"""
        article = db.query(Article).filter(Article.id == article_id).first()
        if article:
            article.title = title
            article.content = content
            db.commit()
            db.refresh(article)
            logger.info(f"已更新文章: {article_id}")
            return article
        return None
    
    @staticmethod
    def start_scheduled_publish(db: Session) -> dict:
        """业务模块说明。"""
        config = ArticleService.get_generation_config(db)
        success = start_scheduled_publish(config["frequency_unit"], config["frequency_value"])
        if success:
            return {"success": True, "message": "定时发布已启动"}
        return {"success": False, "message": "启动定时发布失败"}
    
    @staticmethod
    def stop_scheduled_publish() -> dict:
        """业务模块说明。"""
        success = stop_scheduled_publish()
        if success:
            return {"success": True, "message": "定时发布已停止"}
        return {"success": False, "message": "停止定时发布失败"}
    
    @staticmethod
    def get_scheduled_publish_status() -> dict:
        """业务模块说明。"""
        return get_scheduled_publish_status()
