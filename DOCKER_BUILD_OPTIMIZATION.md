# Docker 构建优化说明

## 🚀 已优化的内容

### 1. 国内镜像源配置

#### apt-get 镜像源（阿里云）
- 自动替换 Debian 官方源为阿里云镜像
- 支持多种 Debian 版本（bookworm, bullseye 等）

#### pip 镜像源（清华大学）
- 使用清华 PyPI 镜像：`https://pypi.tuna.tsinghua.edu.cn/simple`
- 设置超时时间为 60 秒

### 2. 构建上下文优化

#### .dockerignore 已排除的大目录
- `.git/` (12GB)
- `results/` (11GB)
- `test_data/` (38GB)
- `uploads/` (65MB)
- `data/` (16KB)

#### 排除的文件类型
- 所有大文件：`.h5ad`, `.fastq`, `.bam`, `.vcf`, `.mtx`, `.tar.gz`, `.zip`
- 临时文件：`*.log`, `*.tmp`, `*.cache`
- IDE 配置：`.vscode/`, `.idea/`

### 3. Dockerfile 层缓存优化

构建顺序（利用 Docker 层缓存）：
1. 安装系统依赖（很少变化）
2. 配置镜像源（很少变化）
3. 复制 `requirements.txt`（偶尔变化）
4. 安装 Python 依赖（只有 requirements.txt 变化时才重建）
5. 复制代码（代码变化时才重建）

## 📊 构建速度对比

### 优化前
- 构建上下文：~39.79GB
- apt-get 下载：从国外源，速度慢
- pip 安装：从 PyPI 官方源，速度慢
- 预计构建时间：10-20 分钟

### 优化后
- 构建上下文：<100MB（排除大文件后）
- apt-get 下载：从阿里云镜像，速度快
- pip 安装：从清华镜像，速度快
- 预计构建时间：2-5 分钟

## 🔧 使用方法

### 重新构建（使用优化后的配置）

```bash
# 停止当前构建（如果正在运行）
# Ctrl+C

# 重新构建（会使用新的镜像源和 .dockerignore）
docker compose build --no-cache

# 或者只构建特定服务
docker compose build api-server
```

### 验证镜像源

构建时查看日志，应该看到：
- apt-get 从 `mirrors.aliyun.com` 下载
- pip 从 `pypi.tuna.tsinghua.edu.cn` 下载

## ⚠️ 注意事项

1. **首次构建**：即使使用镜像源，首次构建仍需要下载所有依赖，可能需要 3-5 分钟
2. **后续构建**：如果只修改代码，Docker 会使用缓存，只需几秒钟
3. **网络问题**：如果镜像源不可用，可以临时切换回官方源

## 🔄 切换镜像源（如果需要）

### 切换到其他国内镜像源

**apt-get（阿里云 → 清华）**：
```dockerfile
# 在 Dockerfile 中替换
sed -i 's|mirrors.aliyun.com|mirrors.tuna.tsinghua.edu.cn|g'
```

**pip（清华 → 阿里云）**：
```dockerfile
# 在 Dockerfile 中替换
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
```

