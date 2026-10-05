"""业务模块说明。"""
import pytest
import tempfile
import os


class TestKnowledgeBaseAPI:
    """业务模块说明。"""
    
    def test_get_knowledge_base_list_empty(self, client):
        """业务模块说明。"""
        response = client.get("/api/knowledge-base/list")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0
    
    def test_scan_nonexistent_folder(self, client):
        """业务模块说明。"""
        response = client.post("/api/knowledge-base/scan", json={
            "folder_path": "/nonexistent/path/12345"
        })
        assert response.status_code == 400
    
    def test_scan_folder_with_txt_files(self, client):
        """业务模块说明。"""
        # 创建临时目录和文件
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试txt文件
            txt_path = os.path.join(tmpdir, "test.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("这是测试内容")
            
            response = client.post("/api/knowledge-base/scan", json={
                "folder_path": tmpdir
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["processed"] == 1
    
    def test_scan_folder_skip_existing(self, client):
        """业务模块说明。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = os.path.join(tmpdir, "test.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("测试内容")
            
            # 第一次扫描
            client.post("/api/knowledge-base/scan", json={"folder_path": tmpdir})
            
            # 第二次扫描应该跳过
            response = client.post("/api/knowledge-base/scan", json={"folder_path": tmpdir})
            data = response.json()
            assert data["data"]["processed"] == 0
            assert data["data"]["skipped"] == 1
    
    def test_get_knowledge_base_detail(self, client):
        """业务模块说明。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = os.path.join(tmpdir, "test.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("详情测试内容")
            
            # 扫描
            client.post("/api/knowledge-base/scan", json={"folder_path": tmpdir})
            
            # 获取列表
            list_response = client.get("/api/knowledge-base/list")
            kb_id = list_response.json()["data"][0]["id"]
            
            # 获取详情
            response = client.get(f"/api/knowledge-base/{kb_id}")
            assert response.status_code == 200
            data = response.json()
            assert "详情测试内容" in data["data"]["content"]
    
    def test_delete_knowledge_base(self, client):
        """业务模块说明。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = os.path.join(tmpdir, "test.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("待删除内容")
            
            # 扫描
            client.post("/api/knowledge-base/scan", json={"folder_path": tmpdir})
            
            # 获取ID
            list_response = client.get("/api/knowledge-base/list")
            kb_id = list_response.json()["data"][0]["id"]
            
            # 删除
            response = client.delete(f"/api/knowledge-base/{kb_id}")
            assert response.status_code == 200
            
            # 确认已删除
            list_response = client.get("/api/knowledge-base/list")
            assert len(list_response.json()["data"]) == 0
    
    def test_clear_all_knowledge_base(self, client):
        """业务模块说明。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建多个文件
            for i in range(3):
                txt_path = os.path.join(tmpdir, f"test{i}.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"内容{i}")
            
            # 扫描
            client.post("/api/knowledge-base/scan", json={"folder_path": tmpdir})
            
            # 确认有3条记录
            list_response = client.get("/api/knowledge-base/list")
            assert len(list_response.json()["data"]) == 3
            
            # 清空
            response = client.delete("/api/knowledge-base")
            assert response.status_code == 200
            
            # 确认已清空
            list_response = client.get("/api/knowledge-base/list")
            assert len(list_response.json()["data"]) == 0
    
    def test_delete_nonexistent_knowledge_base(self, client):
        """业务模块说明。"""
        response = client.delete("/api/knowledge-base/99999")
        assert response.status_code == 404
