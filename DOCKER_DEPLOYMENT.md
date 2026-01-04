# GIBH-AGENT-V2 Docker 化部署指南

## 📋 概述

本项目已支持 Docker 化部署，采用与旧架构类似的微服务架构：
- **NGINX**: 前端网关和反向代理
- **FastAPI + Gunicorn**: API 服务器
- **Celery + Redis**: 异步任务调度
- **Docker Compose**: 一键启动所有服务

## 🏗️ 架构说明

```
用户请求
    ↓
NGINX (端口 8088)
    ↓
FastAPI API Server (端口 8000)
    ├── 同步请求 → 直接处理
    └── 异步任务 → Celery Worker (通过 Redis)
```

## 🚀 快速开始

### 1. 环境准备

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **磁盘空间**: 至少 10GB（用于镜像和数据）

### 2. 配置环境变量（可选）

创建 `.env` 文件（可选，用于覆盖默认配置）：

```bash
# LLM 配置
SILICONFLOW_API_KEY=your_api_key_here
SILICONFLOW_MODEL=Pro/deepseek-ai/DeepSeek-V3.2

# 其他配置
REDIS_URL=redis://redis:6379/0
UPLOAD_DIR=/app/uploads
RESULTS_DIR=/app/results
```

### 3. 启动服务

```bash
# 构建并启动所有服务
docker compose up -d --build

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f api-server
docker compose logs -f worker
```

### 4. 访问服务

- **Web 界面**: http://localhost:8018
- **API 文档**: http://localhost:8018/api/docs
- **Flower (任务监控)**: http://localhost:5555 (如果启用)

### 5. 停止服务

```bash
# 停止所有服务
docker compose down

# 停止并删除数据卷
docker compose down -v
```

## 📁 目录结构

```
GIBH-AGENT-V2/
├── docker-compose.yml          # Docker Compose 配置
├── services/
│   ├── api/
│   │   └── Dockerfile          # API 服务器和 Worker 镜像
│   └── nginx/
│       ├── conf.d/
│       │   └── default.conf    # NGINX 配置
│       └── html/
│           └── index.html      # 前端页面
├── data/
│   ├── uploads/                # 用户上传文件
│   ├── results/                # 分析结果
│   └── redis/                  # Redis 数据持久化
└── gibh_agent/
    └── core/
        ├── celery_app.py       # Celery 配置
        └── tasks.py            # 异步任务定义
```

## 🔧 服务说明

### 1. NGINX (gibh_v2_gateway)

- **端口**: 8088
- **功能**: 
  - 前端静态文件服务
  - API 反向代理
  - 静态资源服务（uploads、results）

### 2. Redis (gibh_v2_redis)

- **端口**: 6379 (内部)
- **功能**: Celery 消息队列和结果后端
- **数据持久化**: `./data/redis/`

### 3. API Server (gibh_v2_api)

- **端口**: 8000 (内部)
- **功能**: FastAPI 应用，处理 HTTP 请求
- **工作进程**: 2 个 Gunicorn Worker

### 4. Worker (gibh_v2_worker)

- **功能**: Celery Worker，处理异步任务
- **并发数**: 4 个 Worker 进程

## 🔄 任务处理流程

### 同步请求（快速响应）

```
用户 → NGINX → API Server → 直接处理 → 返回结果
```

适用于：
- 简单查询
- 文件上传
- 配置获取

### 异步任务（耗时操作）

```
用户 → NGINX → API Server → 提交 Celery 任务 → 立即返回任务 ID
                                                      ↓
                                            Celery Worker → 执行任务 → 存储结果
                                                      ↓
                                            用户轮询或 WebSocket → 获取结果
```

适用于：
- 工作流执行
- 大数据分析
- 长时间运行的任务

## 📝 修改 server.py 以支持 Celery（可选）

当前 `server.py` 是同步执行的。如果需要将工作流执行改为异步，可以修改：

```python
from gibh_agent.core.tasks import execute_workflow_task

# 在 /api/execute 端点中
@app.post("/api/execute")
async def execute_workflow(request: dict):
    # 提交到 Celery
    task = execute_workflow_task.delay(
        workflow_config=request.get("workflow_data"),
        file_paths=request.get("file_paths", []),
        output_dir=str(RESULTS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    )
    
    return JSONResponse(content={
        "status": "submitted",
        "task_id": task.id,
        "message": "任务已提交，正在处理中..."
    })
```

## 🐛 故障排查

### 1. 服务无法启动

```bash
# 查看详细日志
docker compose logs

# 检查端口占用
netstat -tulpn | grep 8088
```

### 2. Worker 无法连接 Redis

```bash
# 检查 Redis 状态
docker compose exec redis redis-cli ping

# 检查网络连接
docker compose exec worker ping redis
```

### 3. 任务执行失败

```bash
# 查看 Worker 日志
docker compose logs -f worker

# 查看任务状态（如果启用了 Flower）
# 访问 http://localhost:5555
```

## 🔐 安全建议

1. **生产环境**：
   - 修改默认端口
   - 配置 HTTPS
   - 限制 API 访问
   - 使用环境变量管理敏感信息

2. **数据安全**：
   - 定期备份 `data/` 目录
   - 配置 Redis 密码
   - 限制文件上传大小

## 📚 参考

- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Celery 文档](https://docs.celeryproject.org/)
- [NGINX 文档](https://nginx.org/en/docs/)

