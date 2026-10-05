# AI文章自动生成系统 - 后端 API 服务
# 使用 uv 进行依赖管理
#
# 注意：桌面 GUI 应用需要在本地运行，不在 Docker 中
# Docker 仅用于运行后端 API 服务

FROM python:3.11-slim as builder

WORKDIR /app

# 安装 uv（Python 依赖管理工具）
RUN pip install --no-cache-dir uv

# 复制项目配置文件
COPY pyproject.toml ./

# 使用 uv 安装依赖（排除 GUI 相关包以减小镜像体积）
# 注意：PySide6 不安装在 Docker 中，因为 GUI 需要本地运行
RUN uv pip install --system \
    fastapi uvicorn sqlalchemy pydantic pydantic-settings \
    python-dotenv requests apscheduler \
    PyPDF2 pdfplumber pymupdf python-docx openpyxl \
    python-multipart aiofiles

# 运行阶段
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制已安装的包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码（排除 GUI 目录）
COPY app/ ./app/
COPY main.py ./
COPY pyproject.toml ./
COPY init_data.sql schema.sql ./

# 创建必要的目录
RUN mkdir -p data logs

# 设置环境变量
ENV DOCKER_ENV=true
ENV PYTHONPATH=/app

# 暴露 API 端口
EXPOSE 8000

# 启动 API 服务
CMD ["python", "main.py"]
