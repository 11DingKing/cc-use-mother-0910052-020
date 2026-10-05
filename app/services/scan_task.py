"""业务模块说明。"""
import threading
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScanTask:
    id: str
    folder_path: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    total_files: int = 0
    processed: int = 0
    skipped: int = 0
    errors: list = field(default_factory=list)
    message: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class ScanTaskManager:
    """业务模块说明。"""
    _tasks: dict[str, ScanTask] = {}
    _lock = threading.Lock()
    
    @classmethod
    def create_task(cls, folder_path: str) -> ScanTask:
        task_id = str(uuid.uuid4())[:8]
        task = ScanTask(id=task_id, folder_path=folder_path)
        with cls._lock:
            cls._tasks[task_id] = task
        return task
    
    @classmethod
    def get_task(cls, task_id: str) -> Optional[ScanTask]:
        return cls._tasks.get(task_id)
    
    @classmethod
    def update_task(cls, task_id: str, **kwargs):
        with cls._lock:
            task = cls._tasks.get(task_id)
            if task:
                for key, value in kwargs.items():
                    setattr(task, key, value)
    
    @classmethod
    def cleanup_old_tasks(cls, max_age_hours: int = 1):
        """业务模块说明。"""
        now = datetime.now()
        with cls._lock:
            to_delete = [
                tid for tid, task in cls._tasks.items()
                if task.completed_at and (now - task.completed_at).total_seconds() > max_age_hours * 3600
            ]
            for tid in to_delete:
                del cls._tasks[tid]
