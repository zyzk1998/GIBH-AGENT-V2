#!/bin/bash
# 快速检查 API 服务器

echo "⏳ 等待服务启动（5秒）..."
sleep 5

echo ""
echo "📊 容器状态："
docker compose ps api-server

echo ""
echo "📋 最近日志（最后 30 行）："
docker compose logs api-server --tail 30

echo ""
echo "🔍 测试连接："
if curl -s http://localhost:8028/api/docs > /dev/null 2>&1; then
    echo "✅ API 服务器响应正常！"
    echo "   访问地址: http://localhost:8028"
else
    echo "❌ API 服务器无响应"
    echo ""
    echo "可能的原因："
    echo "1. 服务还在启动中，请再等待 10-20 秒"
    echo "2. 查看完整日志: docker compose logs api-server"
    echo "3. 如果看到错误，可能需要重新构建: docker compose build --no-cache"
fi

