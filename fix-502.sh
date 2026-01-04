#!/bin/bash
# 502 错误自动修复脚本

set -e

echo "🔧 GIBH-AGENT-V2 502 错误自动修复"
echo "=================================="
echo ""

echo "1️⃣ 停止所有容器..."
docker compose down
echo ""

echo "2️⃣ 检查 requirements.txt 是否包含 paramiko..."
if grep -q "paramiko" requirements.txt; then
    echo "✅ paramiko 已在 requirements.txt 中"
else
    echo "❌ paramiko 缺失，正在添加..."
    echo "paramiko>=3.0.0" >> requirements.txt
    echo "✅ 已添加 paramiko"
fi
echo ""

echo "3️⃣ 清理旧镜像（可选）..."
read -p "是否删除旧镜像以强制重新构建？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi gibh-v2-api:latest 2>/dev/null || echo "镜像不存在，跳过删除"
fi
echo ""

echo "4️⃣ 重新构建镜像（使用国内镜像源）..."
docker compose build --no-cache
echo ""

echo "5️⃣ 启动所有服务..."
docker compose up -d
echo ""

echo "6️⃣ 等待服务启动（10秒）..."
sleep 10
echo ""

echo "7️⃣ 检查容器状态..."
docker compose ps
echo ""

echo "8️⃣ 查看 API 服务器启动日志（最近 30 行）..."
docker compose logs api-server --tail 30
echo ""

echo "9️⃣ 测试 API 服务器..."
if docker compose exec -T api-server curl -s http://localhost:8000/api/docs > /dev/null 2>&1; then
    echo "✅ API 服务器响应正常"
else
    echo "❌ API 服务器无响应，查看详细日志："
    echo "   docker compose logs api-server"
fi
echo ""

echo "✅ 修复完成！"
echo ""
echo "📋 下一步："
echo "   1. 访问 http://localhost:8018 测试前端"
echo "   2. 如果仍有问题，查看完整日志："
echo "      docker compose logs -f api-server"
echo ""

