"""业务模块说明。"""
import threading
import logging
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# 全局任务状态
_generation_task = {
    "task_id": None,
    "status": "idle",  # idle, running, completed, failed
    "total": 0,
    "completed": 0,
    "current_title": "",
    "articles": [],
    "errors": [],
    "started_at": None,
    "finished_at": None,
    # 任务参数（用于前端恢复状态）
    "params": {
        "count": 0,
        "keyword_ids": [],
        "use_knowledge_base": True
    }
}
_task_lock = threading.Lock()


def get_task_status() -> dict:
    """业务模块说明。"""
    with _task_lock:
        return _generation_task.copy()


def start_generation_task(
    count: int,
    keyword_ids: Optional[List[int]],
    use_knowledge_base: bool
) -> dict:
    """业务模块说明。"""
    global _generation_task
    
    with _task_lock:
        if _generation_task["status"] == "running":
            return {"success": False, "message": "已有任务在运行中"}
        
        task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        _generation_task = {
            "task_id": task_id,
            "status": "running",
            "total": count,
            "completed": 0,
            "current_title": "准备中...",
            "articles": [],
            "errors": [],
            "started_at": datetime.now().isoformat(),
            "finished_at": None,
            "cancelled": False,
            "params": {
                "count": count,
                "keyword_ids": keyword_ids or [],
                "use_knowledge_base": use_knowledge_base
            }
        }
    
    # 启动后台线程
    thread = threading.Thread(
        target=_generation_worker,
        args=(task_id, count, keyword_ids, use_knowledge_base),
        daemon=True
    )
    thread.start()
    
    return {"success": True, "task_id": task_id}


def _generation_worker(
    task_id: str,
    count: int,
    keyword_ids: Optional[List[int]],
    use_knowledge_base: bool
):
    """业务模块说明。"""
    global _generation_task
    
    from app.core.database import SessionLocal
    from app.models.article import Article
    from app.models.keyword import Keyword
    from app.services.keyword_service import KeywordService
    from app.services.knowledge_base_service import KnowledgeBaseService
    from app.services.deepseek_service import DeepSeekService
    
    db = SessionLocal()
    
    try:
        # 获取关键词
        keywords = []
        if keyword_ids:
            keywords = [kw.keyword for kw_id in keyword_ids 
                       for kw in [db.query(Keyword).filter(Keyword.id == kw_id).first()] if kw]
        
        # 如果没有指定关键词，获取所有关键词
        all_keywords = KeywordService.get_all_keywords(db) if not keywords else keywords
        
        # 获取知识库内容
        knowledge_base_content = ""
        if use_knowledge_base:
            knowledge_base_content = KnowledgeBaseService.get_all_content(db)
        
        # 验证触发条件：至少需要关键词或知识库中的一项
        if not all_keywords and not knowledge_base_content:
            with _task_lock:
                _generation_task["status"] = "failed"
                _generation_task["errors"].append("至少需要指定关键词或知识库中的一项才能生成文章")
                _generation_task["finished_at"] = datetime.now().isoformat()
            logger.error("生成失败：没有关键词和知识库内容")
            return
        
        for i in range(count):
            # 检查任务是否被取消
            with _task_lock:
                if _generation_task["task_id"] != task_id or _generation_task.get("cancelled", False):
                    logger.info("任务已取消")
                    return
            
            try:
                logger.info(f"开始生成第 {i+1}/{count} 篇文章")
                
                # 获取已生成的标题列表（避免重复）
                with _task_lock:
                    existing_titles = [a["title"] for a in _generation_task["articles"]]
                
                # 一次性生成标题和内容（合并调用，减少等待时间）
                with _task_lock:
                    _generation_task["current_title"] = f"正在生成第 {i+1}/{count} 篇..."
                
                result = DeepSeekService.generate_article(
                    keywords=all_keywords,
                    knowledge_base_content=knowledge_base_content,
                    existing_titles=existing_titles
                )
                
                title = result["title"]
                content = result["content"]
                
                # 保存文章
                article = Article(
                    title=title,
                    content=content,
                    status="pending"
                )
                db.add(article)
                db.commit()
                db.refresh(article)
                
                with _task_lock:
                    _generation_task["completed"] = i + 1
                    _generation_task["articles"].append({
                        "id": article.id,
                        "title": title
                    })
                
                logger.info(f"文章生成成功: {article.id} - {title[:50]}")
                
            except Exception as e:
                error_msg = f"生成第 {i+1} 篇文章失败: {str(e)}"
                logger.error(error_msg, exc_info=True)
                with _task_lock:
                    _generation_task["completed"] = i + 1
                    _generation_task["errors"].append(error_msg)
        
        # 完成
        with _task_lock:
            _generation_task["status"] = "completed"
            _generation_task["current_title"] = "生成完成"
            _generation_task["finished_at"] = datetime.now().isoformat()
        
        logger.info(f"文章生成任务完成: {len(_generation_task['articles'])} 篇成功")
        
    except Exception as e:
        logger.error(f"生成任务失败: {e}", exc_info=True)
        with _task_lock:
            _generation_task["status"] = "failed"
            _generation_task["errors"].append(str(e))
            _generation_task["finished_at"] = datetime.now().isoformat()
    finally:
        db.close()


def cancel_task() -> dict:
    """业务模块说明。"""
    global _generation_task
    with _task_lock:
        if _generation_task["status"] == "running":
            _generation_task["cancelled"] = True
            _generation_task["status"] = "idle"
            _generation_task["task_id"] = None
            return {"success": True, "message": "任务已取消"}
        # 重置状态
        _generation_task["status"] = "idle"
        _generation_task["task_id"] = None
        _generation_task["cancelled"] = False
        return {"success": True, "message": "任务状态已重置"}
