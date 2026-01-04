FROM python:3.9-slim

WORKDIR /app

# 使用国内镜像源加速 apt-get（阿里云镜像）
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
        sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list; \
    else \
        echo "deb https://mirrors.aliyun.com/debian/ bookworm main" > /etc/apt/sources.list && \
        echo "deb https://mirrors.aliyun.com/debian/ bookworm-updates main" >> /etc/apt/sources.list && \
        echo "deb https://mirrors.aliyun.com/debian-security/ bookworm-security main" >> /etc/apt/sources.list; \
    fi

# 安装系统级依赖（编译生信库需要）
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libhdf5-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 配置 pip 使用国内镜像源（清华大学镜像，速度更快）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip config set global.timeout 60

# 先复制依赖文件（利用 Docker 层缓存）
COPY requirements.txt .

# 安装 Python 依赖（这一层会被缓存，除非 requirements.txt 改变）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 最后复制项目代码（代码变化时只需要重新构建这一层）
# 使用 .dockerignore 排除大文件，只复制必要的代码
COPY gibh_agent/ /app/gibh_agent/
COPY server.py /app/

# 创建必要的目录
RUN mkdir -p /app/uploads /app/results /app/data

# 暴露端口
EXPOSE 8028

# 默认命令（会被 docker-compose 覆盖）
CMD ["python", "server.py"]

