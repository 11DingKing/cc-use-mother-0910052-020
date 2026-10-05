"""业务模块说明。"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from app.core.config import settings


def setup_logging(mode: str = "api"):
    """业务模块说明。"""
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{mode}.log")
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=settings.LOG_BACKUP_DAYS,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logging.info(f"日志系统已初始化，模式: {mode}, 日志文件: {log_file}")
    
    return logger


def get_logger(name: str):
    """业务模块说明。"""
    return logging.getLogger(name)
