"""业务模块说明。"""
import pytest


class TestConfigAPI:
    """业务模块说明。"""
    
    def test_get_deepseek_config(self, client):
        """业务模块说明。"""
        response = client.get("/api/config/deepseek")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api_url" in data["data"]
        assert "timeout" in data["data"]
    
    def test_update_deepseek_config(self, client):
        """业务模块说明。"""
        response = client.put("/api/config/deepseek", json={
            "api_key": "sk-test-key-12345",
            "api_url": "https://api.deepseek.com/v1/chat/completions",
            "timeout": 120
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "配置更新成功"
    
    def test_update_deepseek_config_partial(self, client):
        """业务模块说明。"""
        response = client.put("/api/config/deepseek", json={
            "api_key": "sk-new-key"
        })
        assert response.status_code == 200
