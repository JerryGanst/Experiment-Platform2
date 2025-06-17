# 使用Python 3.9官方镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件（如果存在）
COPY requirements.txt* ./

# 安装Python依赖
RUN pip install --no-cache-dir pandas openpyxl

# 复制应用代码
COPY . .

# 创建输出目录
RUN mkdir -p /app/output

# 设置权限
RUN chmod +x markdown.py

# 暴露端口（如果需要web服务）
EXPOSE 8000

# 默认命令
CMD ["python", "markdown.py", "--help"]

# 使用示例：
# docker build -t excel-to-markdown .
# docker run -v $(pwd)/file:/app/input -v $(pwd)/output:/app/output excel-to-markdown python markdown.py input/your_file.xlsx 