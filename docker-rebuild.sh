#!/bin/bash
# Docker 重新构建脚本（解决镜像已存在的问题）

set -e

echo "🔧 清理旧镜像和容器..."
sudo docker compose down 2>/dev/null || true

echo "🗑️ 删除旧镜像..."
sudo docker rmi gibh-v2-api:latest 2>/dev/null || echo "镜像不存在，跳过删除"

echo "🔨 重新构建镜像（使用国内镜像源）..."
sudo docker compose build --no-cache --pull

echo "✅ 构建完成！"
echo ""
echo "🚀 启动服务："
echo "   sudo docker compose up -d"

