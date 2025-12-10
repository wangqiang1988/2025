# 使用官方的 Python 基础镜像
FROM python:3.11-slim

# 设置环境变量，以便应用知道在哪里找到上传和转换的文件
ENV UPLOAD_FOLDER /app/data/uploads
ENV OUTPUT_FOLDER /app/data/outputs
ENV MAX_FILE_SIZE 20 * 1024 * 1024  # 20 MB

# 1. 安装 FFmpeg 依赖
# FFmpeg 是处理视频和音频转换的核心工具
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 2. 设置工作目录
WORKDIR /app

# 3. 复制 Python 依赖并安装
# 假设您的依赖文件名为 requirements.txt (内容只需 'Flask')
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 复制应用程序代码（包括 Python 后端文件和前端模板/静态文件）
# 假设结构:
# - app.py (主应用文件)
# - templates/ (HTML 模板)
# - static/ (CSS/JS/Images)
COPY . .

# 5. 创建存储文件夹并赋予权限
RUN mkdir -p $UPLOAD_FOLDER $OUTPUT_FOLDER

# 6. 暴露应用端口 (Flask 默认 5000)
EXPOSE 5000

# 7. 启动 Flask 应用
# 确保在生产环境中，使用 Gunicorn 或 Waitress 等 WSGI 服务器运行
# 这里为了简化示例使用 Flask 内建服务器
CMD ["python", "app.py"]