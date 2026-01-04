# 🐳 GIBH-AGENT-V2 Docker 化部署

## ✅ 已完成的工作

已成功将 GIBH-AGENT-V2 改造为 Docker 化部署，采用与旧架构类似的微服务架构。

## 📦 创建的文件

1. **docker-compose.yml** - Docker Compose 编排文件
2. **services/api/Dockerfile** - API 服务器和 Worker 镜像
3. **services/nginx/conf.d/default.conf** - NGINX 反向代理配置
4. **gibh_agent/core/celery_app.py** - Celery 应用配置
5. **gibh_agent/core/tasks.py** - 异步任务定义
6. **.dockerignore** - Docker 构建忽略文件
7. **DOCKER_DEPLOYMENT.md** - 详细部署文档

## 🚀 快速启动

```bash
# 1. 构建并启动所有服务
docker compose up -d --build

# 2. 查看服务状态
docker compose ps

# 3. 查看日志
docker compose logs -f

# 4. 访问服务
# Web 界面: http://localhost:8088
# API 文档: http://localhost:8088/api/docs
```

## 🏗️ 架构对比

### 旧架构 (GIBH-AGENT)
- NGINX 网关
- FastAPI + Gunicorn
- Celery + Redis
- vLLM 推理引擎（双脑）

### 新架构 (GIBH-AGENT-V2)
- ✅ NGINX 网关
- ✅ FastAPI + Gunicorn
- ✅ Celery + Redis
- ✅ 云端 LLM（SiliconFlow/DeepSeek）
- ✅ 多智能体系统（Router + Domain Agents）

## 📝 注意事项

1. **当前 server.py 仍为同步执行**：如需异步执行，参考 `server_celery_example.py`
2. **环境变量**：可通过 `.env` 文件配置 API Key 等
3. **数据持久化**：`data/` 目录会持久化保存
4. **端口映射**：默认使用 8088 端口（可在 docker-compose.yml 中修改）

## 🔧 下一步（可选）

如需将工作流执行改为异步，可以：
1. 参考 `server_celery_example.py` 修改 `server.py`
2. 添加任务状态查询端点
3. 可选：集成 Flower 进行任务监控

详细说明请参考 `DOCKER_DEPLOYMENT.md`。

