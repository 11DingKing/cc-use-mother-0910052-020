"""业务模块说明。"""
import pytest


class TestKeywordsAPI:
    """业务模块说明。"""
    
    def test_create_keywords(self, client):
        """业务模块说明。"""
        response = client.post("/api/keywords", json={
            "keywords": ["SEO优化", "网站建设", "数字营销"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["created"] == 3
        assert data["data"]["skipped"] == 0
    
    def test_create_duplicate_keywords(self, client):
        """业务模块说明。"""
        # 先创建
        client.post("/api/keywords", json={"keywords": ["SEO优化"]})
        # 再次创建相同关键词
        response = client.post("/api/keywords", json={"keywords": ["SEO优化", "新关键词"]})
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["created"] == 1
        assert data["data"]["skipped"] == 1
    
    def test_get_keywords_list(self, client):
        """业务模块说明。"""
        # 先创建一些关键词
        client.post("/api/keywords", json={"keywords": ["关键词1", "关键词2"]})
        
        response = client.get("/api/keywords")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
    
    def test_get_keyword_detail(self, client):
        """业务模块说明。"""
        # 先创建
        client.post("/api/keywords", json={"keywords": ["测试关键词"]})
        
        # 获取列表找到ID
        list_response = client.get("/api/keywords")
        keyword_id = list_response.json()["data"][0]["id"]
        
        # 获取详情
        response = client.get(f"/api/keywords/{keyword_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["keyword"] == "测试关键词"
    
    def test_update_keyword(self, client):
        """业务模块说明。"""
        # 先创建
        client.post("/api/keywords", json={"keywords": ["原关键词"]})
        
        # 获取ID
        list_response = client.get("/api/keywords")
        keyword_id = list_response.json()["data"][0]["id"]
        
        # 更新
        response = client.put(f"/api/keywords/{keyword_id}", json={"keyword": "新关键词"})
        assert response.status_code == 200
        assert response.json()["data"]["keyword"] == "新关键词"
    
    def test_delete_keyword(self, client):
        """业务模块说明。"""
        # 先创建
        client.post("/api/keywords", json={"keywords": ["待删除"]})
        
        # 获取ID
        list_response = client.get("/api/keywords")
        keyword_id = list_response.json()["data"][0]["id"]
        
        # 删除
        response = client.delete(f"/api/keywords/{keyword_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 确认已删除
        list_response = client.get("/api/keywords")
        assert len(list_response.json()["data"]) == 0
    
    def test_delete_nonexistent_keyword(self, client):
        """业务模块说明。"""
        response = client.delete("/api/keywords/99999")
        assert response.status_code == 404
