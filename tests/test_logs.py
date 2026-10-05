"""业务模块说明。"""
import pytest


class TestLogsAPI:
    """业务模块说明。"""
    
    def test_get_logs_list_empty(self, client):
        """业务模块说明。"""
        response = client.get("/api/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0
    
    def test_get_logs_with_article_filter(self, client):
        """业务模块说明。"""
        response = client.get("/api/logs?article_id=1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_log_detail(self, client, db):
        """业务模块说明。"""
        from app.models.publish_log import PublishLog
        from app.models.article import Article
        
        # 先创建文章
        article = Article(title="测试", content="内容", status="pending")
        db.add(article)
        db.commit()
        db.refresh(article)
        
        # 创建日志
        log = PublishLog(
            article_id=article.id,
            status="success"
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        
        response = client.get(f"/api/logs/{log.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "success"
    
    def test_get_nonexistent_log(self, client):
        """业务模块说明。"""
        response = client.get("/api/logs/99999")
        assert response.status_code == 404
