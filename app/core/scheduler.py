"""业务模块说明。"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 创建调度器
scheduler = AsyncIOScheduler(
    jobstores={'default': MemoryJobStore()},
    executors={'default': ThreadPoolExecutor(20)},
    job_defaults={
        'coalesce': False,
        'max_instances': 1
    }
)

# 定时发布任务ID
SCHEDULED_PUBLISH_JOB_ID = "scheduled_publish_job"


def publish_pending_articles():
    """业务模块说明。"""
    from app.core.database import SessionLocal
    from app.models.article import Article
    from app.models.publish_log import PublishLog
    from app.models.system_config import SystemConfig
    from app.services.cms_service import CMSServiceFactory
    
    db = SessionLocal()
    try:
        # 获取配置的每次发布数量（独立于生成数量），默认为1
        publish_count = 1
        config = db.query(SystemConfig).filter(SystemConfig.config_key == "publish_count").first()
        if config:
            try:
                publish_count = int(config.config_value)
            except (ValueError, TypeError):
                publish_count = 1
        
        # 获取待发布的文章（按配置数量）
        articles = db.query(Article).filter(Article.status == "pending").limit(publish_count).all()
        if not articles:
            logger.info("没有待发布的文章")
            return
        
        logger.info(f"定时发布任务开始，计划发布 {len(articles)} 篇文章")
        
        success_count = 0
        fail_count = 0
        
        for article in articles:
            logger.info(f"定时发布文章: {article.id} - {article.title[:50]}")
            
            try:
                result = CMSServiceFactory.publish_article(
                    db, article.id, article.title, article.content
                )
                
                if result["success"]:
                    article.status = "published"
                    article.published_at = datetime.now()
                    db.commit()
                    
                    log = PublishLog(
                        article_id=article.id,
                        status="success"
                    )
                    db.add(log)
                    db.commit()
                    
                    logger.info(f"定时发布成功: {article.id}")
                    success_count += 1
                else:
                    raise Exception(result.get("message", "发布失败"))
                    
            except Exception as e:
                article.status = "failed"
                db.commit()
                
                log = PublishLog(
                    article_id=article.id,
                    status="failed",
                    error_message=str(e)
                )
                db.add(log)
                db.commit()
                
                logger.error(f"定时发布失败: {article.id} - {e}")
                fail_count += 1
        
        logger.info(f"定时发布任务完成: 成功 {success_count} 篇, 失败 {fail_count} 篇")
    finally:
        db.close()


def start_scheduled_publish(frequency_unit: str, frequency_value: int):
    """业务模块说明。"""
    # 先停止现有任务
    stop_scheduled_publish()
    
    # 构建触发器参数
    trigger_kwargs = {}
    if frequency_unit == "minute":
        trigger_kwargs["minutes"] = frequency_value
    elif frequency_unit == "hour":
        trigger_kwargs["hours"] = frequency_value
    elif frequency_unit == "day":
        trigger_kwargs["days"] = frequency_value
    else:
        logger.error(f"无效的频率单位: {frequency_unit}")
        return False
    
    # 添加定时任务
    scheduler.add_job(
        publish_pending_articles,
        trigger=IntervalTrigger(**trigger_kwargs),
        id=SCHEDULED_PUBLISH_JOB_ID,
        name="定时发布文章",
        replace_existing=True
    )
    
    logger.info(f"定时发布任务已启动: 每 {frequency_value} {frequency_unit}")
    return True


def stop_scheduled_publish():
    """业务模块说明。"""
    try:
        job = scheduler.get_job(SCHEDULED_PUBLISH_JOB_ID)
        if job:
            scheduler.remove_job(SCHEDULED_PUBLISH_JOB_ID)
            logger.info("定时发布任务已停止")
            return True
    except Exception as e:
        logger.error(f"停止定时任务失败: {e}")
    return False


def get_scheduled_publish_status():
    """业务模块说明。"""
    job = scheduler.get_job(SCHEDULED_PUBLISH_JOB_ID)
    if job:
        return {
            "running": True,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        }
    return {"running": False, "next_run_time": None}
