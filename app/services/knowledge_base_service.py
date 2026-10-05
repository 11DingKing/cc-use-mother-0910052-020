"""业务模块说明。"""
import os
import logging
import threading
from typing import List, Optional
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime

from app.models.knowledge_base import KnowledgeBase
from app.core.exceptions import FileReadException
from app.services.file_parser import FileParser
from app.services.scan_task import ScanTaskManager, TaskStatus, ScanTask
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """业务模块说明。"""
    
    @staticmethod
    def start_scan_async(folder_path: str) -> ScanTask:
        """业务模块说明。"""
        if not os.path.exists(folder_path):
            raise FileReadException(f"文件夹不存在: {folder_path}")
        
        if not os.path.isdir(folder_path):
            raise FileReadException(f"路径不是文件夹: {folder_path}")
        
        task = ScanTaskManager.create_task(folder_path)
        
        # 启动后台线程
        thread = threading.Thread(
            target=KnowledgeBaseService._scan_worker,
            args=(task.id, folder_path),
            daemon=True
        )
        thread.start()
        
        return task
    
    @staticmethod
    def _scan_worker(task_id: str, folder_path: str):
        """业务模块说明。"""
        db = SessionLocal()
        try:
            ScanTaskManager.update_task(task_id, status=TaskStatus.RUNNING, message="正在扫描文件...")
            
            folder_path = os.path.abspath(folder_path)
            logger.info(f"开始扫描文件夹: {folder_path}")
            
            # 支持的文件类型
            supported_exts = FileParser.get_supported_extensions()
            all_files = []
            
            for ext in supported_exts:
                pattern = f"*{ext}"
                all_files.extend([(f, ext[1:]) for f in Path(folder_path).rglob(pattern)])
            
            total_files = len(all_files)
            ScanTaskManager.update_task(task_id, total_files=total_files)
            
            processed = 0
            skipped = 0
            errors = []
            current = 0
            
            for file_path, file_type in all_files:
                current += 1
                progress = int(current / total_files * 100) if total_files > 0 else 100
                ScanTaskManager.update_task(
                    task_id, 
                    progress=progress,
                    message=f"正在处理: {file_path.name}"
                )
                
                try:
                    file_path_str = str(file_path)
                    existing = db.query(KnowledgeBase).filter(
                        KnowledgeBase.file_path == file_path_str
                    ).first()
                    
                    if existing:
                        skipped += 1
                        continue
                    
                    content = FileParser.parse(file_path_str)
                    
                    if content:
                        kb = KnowledgeBase(
                            file_path=file_path_str,
                            file_type=file_type,
                            content=content
                        )
                        db.add(kb)
                        processed += 1
                        logger.info(f"已处理文件: {file_path_str}")
                except Exception as e:
                    error_msg = f"处理文件失败 {file_path}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            db.commit()
            
            ScanTaskManager.update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                processed=processed,
                skipped=skipped,
                errors=errors,
                message=f"扫描完成，处理 {processed} 个文件",
                completed_at=datetime.now()
            )
            logger.info(f"扫描任务完成: {task_id}")
            
        except Exception as e:
            logger.error(f"扫描任务失败: {e}")
            ScanTaskManager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                message=str(e),
                completed_at=datetime.now()
            )
        finally:
            db.close()
    
    @staticmethod
    def scan_folder(db: Session, folder_path: str) -> dict:
        """业务模块说明。"""
        if not os.path.exists(folder_path):
            raise FileReadException(f"文件夹不存在: {folder_path}")
        
        if not os.path.isdir(folder_path):
            raise FileReadException(f"路径不是文件夹: {folder_path}")
        
        folder_path = os.path.abspath(folder_path)
        logger.info(f"开始扫描文件夹: {folder_path}")
        
        # 使用统一的文件类型支持
        supported_exts = FileParser.get_supported_extensions()
        all_files = []
        
        for ext in supported_exts:
            pattern = f"*{ext}"
            all_files.extend([(f, ext[1:]) for f in Path(folder_path).rglob(pattern)])
        
        total_files = len(all_files)
        processed = 0
        skipped = 0
        errors = []
        
        for file_path, file_type in all_files:
            try:
                file_path_str = str(file_path)
                # 检查是否已存在
                existing = db.query(KnowledgeBase).filter(
                    KnowledgeBase.file_path == file_path_str
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                # 使用统一的解析方法
                content = FileParser.parse(file_path_str)
                if content:
                    kb = KnowledgeBase(
                        file_path=file_path_str,
                        file_type=file_type,
                        content=content
                    )
                    db.add(kb)
                    processed += 1
                    logger.info(f"已处理文件: {file_path_str}")
            except Exception as e:
                error_msg = f"处理文件失败 {file_path}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        db.commit()
        
        result = {
            "total_files": total_files,
            "processed": processed,
            "skipped": skipped,
            "errors": errors
        }
        
        logger.info(f"扫描完成: {result}")
        return result
    
    @staticmethod
    def get_list(db: Session, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """业务模块说明。"""
        return db.query(KnowledgeBase).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_list_light(db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
        """业务模块说明。"""
        from sqlalchemy import func
        
        results = db.query(
            KnowledgeBase.id,
            KnowledgeBase.file_path,
            KnowledgeBase.file_type,
            func.substr(KnowledgeBase.content, 1, 200).label('content_preview'),
            KnowledgeBase.created_at
        ).offset(skip).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "file_path": r.file_path,
                "file_type": r.file_type,
                "content_preview": (r.content_preview + "...") if r.content_preview and len(r.content_preview) >= 200 else r.content_preview,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
    
    @staticmethod
    def get_stats(db: Session) -> dict:
        """业务模块说明。"""
        from sqlalchemy import func
        
        total = db.query(func.count(KnowledgeBase.id)).scalar() or 0
        
        type_counts = db.query(
            KnowledgeBase.file_type,
            func.count(KnowledgeBase.id)
        ).group_by(KnowledgeBase.file_type).all()
        
        stats = {"total": total, "txt": 0, "pdf": 0, "docx": 0, "xlsx": 0, "md": 0}
        for file_type, count in type_counts:
            if file_type in stats:
                stats[file_type] = count
        
        return stats
    
    @staticmethod
    def get_by_id(db: Session, kb_id: int) -> Optional[KnowledgeBase]:
        """业务模块说明。"""
        return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    @staticmethod
    def get_by_filename(db: Session, filename: str) -> Optional[KnowledgeBase]:
        """业务模块说明。"""
        # 检查 file_path 是否以该文件名结尾（兼容路径扫描和上传两种方式）
        return db.query(KnowledgeBase).filter(
            KnowledgeBase.file_path.endswith(filename)
        ).first()
    
    @staticmethod
    def add_from_upload(db: Session, filename: str, file_type: str, content: str) -> KnowledgeBase:
        """业务模块说明。"""
        # 使用 [上传] 前缀标识上传的文件
        kb = KnowledgeBase(
            file_path=f"[上传] {filename}",
            file_type=file_type,
            content=content
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        logger.info(f"已添加上传文件到知识库: {filename}")
        return kb
    
    @staticmethod
    def delete(db: Session, kb_id: int) -> bool:
        """业务模块说明。"""
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if kb:
            db.delete(kb)
            db.commit()
            logger.info(f"已删除知识库条目: {kb_id}")
            return True
        return False
    
    @staticmethod
    def _extract_key_content(content: str, max_length: int = 3000) -> str:
        """业务模块说明。"""
        if not content or len(content) <= max_length:
            return content
        
        paragraphs = content.split('\n')
        result_parts = []
        current_length = 0
        
        # 第一阶段：保留开头部分（约1/3的空间）
        head_budget = max_length // 3
        for para in paragraphs[:10]:  # 最多取前10个段落
            para = para.strip()
            if not para:
                continue
            if current_length + len(para) > head_budget:
                break
            result_parts.append(para)
            current_length += len(para) + 1
        
        # 第二阶段：提取关键段落（标题、要点等）
        key_markers = ['#', '##', '###', '1.', '2.', '3.', '一、', '二、', '三、', '•', '-', '总结', '结论', '要点']
        remaining_budget = max_length - current_length
        
        for para in paragraphs[10:]:
            para = para.strip()
            if not para or para in result_parts:
                continue
            
            # 检查是否是关键段落
            is_key = any(para.startswith(marker) for marker in key_markers)
            # 较短的段落可能是要点
            is_short = 20 < len(para) < 200
            
            if is_key or is_short:
                if current_length + len(para) > max_length:
                    break
                result_parts.append(para)
                current_length += len(para) + 1
        
        return '\n'.join(result_parts)
    
    @staticmethod
    def get_all_content(db: Session, max_length: int = 50000) -> str:
        """业务模块说明。"""
        kbs = db.query(KnowledgeBase).all()
        if not kbs:
            return ""
        
        contents = []
        total_length = 0
        # 根据文档数量动态分配每个文档的预算
        per_doc_budget = max(2000, max_length // max(len(kbs), 1))
        
        for kb in kbs:
            if total_length >= max_length:
                break
            
            if not kb.content:
                continue
            
            # 智能提取关键内容
            extracted = KnowledgeBaseService._extract_key_content(
                kb.content, 
                min(per_doc_budget, max_length - total_length)
            )
            
            if extracted:
                # 添加文件来源标记
                file_name = os.path.basename(kb.file_path)
                content_with_source = f"[来源: {file_name}]\n{extracted}"
                contents.append(content_with_source)
                total_length += len(content_with_source)
        
        result = "\n\n---\n\n".join(contents)
        return result[:max_length] if len(result) > max_length else result
    
    @staticmethod
    def clear_all(db: Session) -> int:
        """业务模块说明。"""
        count = db.query(KnowledgeBase).count()
        db.query(KnowledgeBase).delete()
        db.commit()
        logger.info(f"已清空知识库，共删除 {count} 条记录")
        return count
