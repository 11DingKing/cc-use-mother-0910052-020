"""业务模块说明。"""
import os
import tempfile
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.scan_task import ScanTaskManager
from app.services.file_parser import FileParser
from app.core.exceptions import FileReadException

router = APIRouter()

# 上传文件大小限制（10MB）
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


class ScanFolderRequest(BaseModel):
    folder_path: str


class ScanFolderResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/scan", response_model=ScanFolderResponse)
async def scan_folder(
    request: ScanFolderRequest,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    try:
        result = KnowledgeBaseService.scan_folder(db, request.folder_path)
        return ScanFolderResponse(
            success=True,
            message="扫描完成",
            data=result
        )
    except FileReadException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动扫描失败: {str(e)}")


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(..., description="支持 txt, pdf, docx, xlsx, md 格式"),
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    if not files:
        raise HTTPException(status_code=400, detail="请选择要上传的文件")
    
    supported_exts = FileParser.get_supported_extensions()
    results = {
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    for file in files:
        try:
            # 检查文件扩展名
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in supported_exts:
                results["failed"] += 1
                results["errors"].append(f"{file.filename}: 不支持的文件格式 {file_ext}")
                continue
            
            # 检查文件大小
            content = await file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                results["failed"] += 1
                results["errors"].append(f"{file.filename}: 文件大小超过限制 (最大 10MB)")
                continue
            
            # 检查是否已存在（按文件名判断）
            existing = KnowledgeBaseService.get_by_filename(db, file.filename)
            if existing:
                results["skipped"] += 1
                continue
            
            # 保存临时文件并解析
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                # 解析文件内容
                parsed_content = FileParser.parse(tmp_path)
                
                if parsed_content:
                    # 保存到知识库（使用上传文件名作为路径标识）
                    KnowledgeBaseService.add_from_upload(
                        db,
                        filename=file.filename,
                        file_type=file_ext[1:],  # 去掉点号
                        content=parsed_content
                    )
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{file.filename}: 文件内容为空")
            finally:
                # 清理临时文件
                os.unlink(tmp_path)
                
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"{file.filename}: {str(e)}")
    
    return {
        "success": True,
        "message": f"上传完成：成功 {results['success']} 个，失败 {results['failed']} 个，跳过 {results['skipped']} 个",
        "data": results
    }


@router.get("/scan/status/{task_id}")
async def get_scan_status(task_id: str):
    """业务模块说明。"""
    task = ScanTaskManager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "success": True,
        "data": {
            "id": task.id,
            "status": task.status.value,
            "progress": task.progress,
            "total_files": task.total_files,
            "processed": task.processed,
            "skipped": task.skipped,
            "errors": task.errors[:5],  # 只返回前5个错误
            "message": task.message
        }
    }


@router.get("/stats")
async def get_knowledge_base_stats(db: Session = Depends(get_db)):
    """业务模块说明。"""
    stats = KnowledgeBaseService.get_stats(db)
    return {"success": True, "data": stats}


@router.get("/list")
async def get_knowledge_base_list(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    items = KnowledgeBaseService.get_list_light(db, skip, limit)
    return {
        "success": True,
        "data": items
    }


@router.get("/{kb_id}")
async def get_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    kb = KnowledgeBaseService.get_by_id(db, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库条目不存在")
    
    return {
        "success": True,
        "data": {
            "id": kb.id,
            "file_path": kb.file_path,
            "file_type": kb.file_type,
            "content": kb.content,
            "created_at": kb.created_at.isoformat() if kb.created_at else None
        }
    }


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    success = KnowledgeBaseService.delete(db, kb_id)
    if not success:
        raise HTTPException(status_code=404, detail="知识库条目不存在")
    
    return {"success": True, "message": "删除成功"}


@router.delete("")
async def clear_knowledge_base(
    db: Session = Depends(get_db)
):
    """业务模块说明。"""
    count = KnowledgeBaseService.clear_all(db)
    return {"success": True, "message": f"已清空 {count} 条知识库记录"}
