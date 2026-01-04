#!/bin/bash
# GIBH-AGENT-V2 Docker 快速启动脚本

set -e

echo "🐳 GIBH-AGENT-V2 Docker 部署脚本"
echo "=================================="

# 检查 Docker 和 Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data/uploads data/results data/redis
mkdir -p services/nginx/html services/nginx/conf.d

# 复制前端文件（如果不存在）
if [ ! -f "services/nginx/html/index.html" ]; then
    if [ -f "index.html" ]; then
        cp index.html services/nginx/html/index.html
        echo "✅ 已复制前端文件"
    fi
fi

# 构建并启动服务
echo ""
echo "🔨 构建 Docker 镜像..."
docker compose build

echo ""
echo "🚀 启动所有服务..."
docker compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态："
docker compose ps

echo ""
echo "✅ 部署完成！"
echo ""
echo "🌐 访问地址："
echo "   - Web 界面: http://localhost:8088"
echo "   - API 文档: http://localhost:8088/api/docs"
echo ""
echo "📋 常用命令："
echo "   - 查看日志: docker compose logs -f"
echo "   - 停止服务: docker compose down"
echo "   - 重启服务: docker compose restart"
echo ""

