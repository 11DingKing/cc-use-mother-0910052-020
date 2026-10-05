"""业务模块说明。"""
import argparse
import sys
import socket
import logging

from app.core.config import settings
from app.api_app import app


def check_port_available(host: str, port: int) -> bool:
    """业务模块说明。"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0
    except Exception:
        return True


def run_api_mode():
    """业务模块说明。"""
    import uvicorn
    
    from app.core.logging import setup_logging
    
    setup_logging(mode="api")
    logger = logging.getLogger(__name__)
    
    if not check_port_available(settings.APP_HOST, settings.APP_PORT):
        logger.error(f"端口 {settings.APP_PORT} 已被占用，请检查是否有其他程序正在使用该端口")
        print(f"错误: 端口 {settings.APP_PORT} 已被占用")
        print("请检查是否有其他程序正在使用该端口，或修改配置使用其他端口")
        sys.exit(1)
    
    logger.info(f"启动 API 服务，监听 {settings.APP_HOST}:{settings.APP_PORT}")
    print(f"API 服务已启动: http://{settings.APP_HOST}:{settings.APP_PORT}")
    print(f"API 文档: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    
    uvicorn.run(
        "app.api_app:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )


def run_gui_mode():
    """业务模块说明。"""
    from PySide6.QtWidgets import QApplication, QMessageBox
    
    from app.core.logging import setup_logging
    from gui.db_manager import db_manager
    from gui.main_window import MainWindow
    from gui.styles import STYLESHEET
    
    setup_logging(mode="gui")
    logger = logging.getLogger(__name__)
    
    logger.info("启动 GUI 模式")
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    
    logger.info("正在初始化数据库连接...")
    if not db_manager.initialize():
        logger.error("数据库连接失败")
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("数据库连接失败")
        msg.setText("无法连接到数据库")
        msg.setInformativeText("请检查数据库配置是否正确，然后重试。")
        msg.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Retry)
        
        result = msg.exec()
        
        if result == QMessageBox.Retry:
            if not db_manager.initialize():
                QMessageBox.critical(
                    None,
                    "错误",
                    "数据库连接仍然失败，程序将退出。\n请检查数据库配置后重新启动。"
                )
                sys.exit(1)
        else:
            sys.exit(1)
    
    logger.info("数据库连接成功")
    
    window = MainWindow()
    window.show()
    
    logger.info("GUI 主窗口已显示")
    
    sys.exit(app.exec())


def main():
    """业务模块说明。"""
    parser = argparse.ArgumentParser(
        description="AI文章自动生成与发布系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py              # 默认启动 API 模式
  python main.py --mode api   # 启动 API 服务
  python main.py --mode gui   # 启动桌面 GUI
        """
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        default="api",
        choices=["api", "gui"],
        help="启动模式: api (API服务) 或 gui (桌面GUI)，默认: api"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="API服务监听地址 (仅API模式有效)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="API服务监听端口 (仅API模式有效)"
    )
    
    args = parser.parse_args()
    
    if args.host:
        settings.APP_HOST = args.host
    if args.port:
        settings.APP_PORT = args.port
    
    if args.mode == "api":
        run_api_mode()
    elif args.mode == "gui":
        run_gui_mode()
    else:
        print(f"未知的启动模式: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
