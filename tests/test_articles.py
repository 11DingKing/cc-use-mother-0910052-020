"""业务模块说明。"""
import pytest
from unittest.mock import patch, MagicMock


class TestArticlesAPI:
    """业务模块说明。"""
    
    def test_get_articles_list_empty(self, client):
        """业务模块说明。"""
        response = client.get("/api/articles")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 0
        assert data["data"]["total"] == 0
        assert "stats" in data["data"]
    
    def test_get_articles_list_with_status_filter(self, client):
        """业务模块说明。"""
        response = client.get("/api/articles?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_generate_articles_without_keywords_or_kb(self, client):
        """业务模块说明。"""
        response = client.post("/api/articles/generate", json={
            "count": 1,
            "use_knowledge_base": True
        })
        # 异步任务会立即返回成功
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_generate_articles_invalid_count(self, client):
        """业务模块说明。"""
        response = client.post("/api/articles/generate", json={
            "count": 0,
            "use_knowledge_base": True
        })
        assert response.status_code == 400
    
    @patch('app.services.deepseek_service.DeepSeekService.generate_title')
    @patch('app.services.deepseek_service.DeepSeekService.generate_content')
    def test_generate_articles_with_keywords(self, mock_content, mock_title, client):
        """业务模块说明。"""
        # Mock DeepSeek API
        mock_title.return_value = "测试文章标题"
        mock_content.return_value = "<p>测试文章内容</p>"
        
        # 先创建关键词
        client.post("/api/keywords", json={"keywords": ["测试关键词"]})
        
        # 生成文章（异步）
        response = client.post("/api/articles/generate", json={
            "count": 1,
            "use_knowledge_base": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "task_id" in data
    
    def test_get_article_detail(self, client, db):
        """业务模块说明。"""
        # 直接在数据库创建文章
        from app.models.article import Article
        article = Article(
            title="测试标题",
            content="<p>测试内容</p>",
            status="pending"
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        
        response = client.get(f"/api/articles/{article.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "测试标题"
    
    def test_get_nonexistent_article(self, client):
        """业务模块说明。"""
        response = client.get("/api/articles/99999")
        assert response.status_code == 404
    
    def test_update_article(self, client, db):
        """业务模块说明。"""
        from app.models.article import Article
        article = Article(
            title="原标题",
            content="原内容",
            status="pending"
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        
        response = client.put(f"/api/articles/{article.id}", json={
            "title": "新标题",
            "content": "新内容"
        })
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "新标题"
    
    def test_delete_article(self, client, db):
        """业务模块说明。"""
        from app.models.article import Article
        article = Article(
            title="待删除",
            content="内容",
            status="pending"
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        
        response = client.delete(f"/api/articles/{article.id}")
        assert response.status_code == 200
        
        # 确认已删除
        response = client.get(f"/api/articles/{article.id}")
        assert response.status_code == 404
    
    def test_get_generation_config(self, client):
        """业务模块说明。"""
        response = client.get("/api/articles/generation-config")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data["data"]
        assert "frequency_unit" in data["data"]
        assert "frequency_value" in data["data"]
    
    def test_update_generation_config(self, client):
        """业务模块说明。"""
        response = client.put("/api/articles/generation-config", json={
            "count": 5,
            "frequency_unit": "hour",
            "frequency_value": 2
        })
        assert response.status_code == 200
        
        # 验证更新
        response = client.get("/api/articles/generation-config")
        data = response.json()
        assert data["data"]["count"] == 5
        assert data["data"]["frequency_unit"] == "hour"
        assert data["data"]["frequency_value"] == 2
    
    def test_update_generation_config_invalid_unit(self, client):
        """业务模块说明。"""
        response = client.put("/api/articles/generation-config", json={
            "count": 1,
            "frequency_unit": "invalid",
            "frequency_value": 1
        })
        assert response.status_code == 400
    
    def test_get_scheduled_publish_status(self, client):
        """业务模块说明。"""
        response = client.get("/api/articles/scheduled-publish/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data["data"]
