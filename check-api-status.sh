#!/bin/bash
# 检查 API 服务器状态

echo "🔍 检查 API 服务器状态"
echo "=================================="
echo ""

echo "1️⃣ 容器状态..."
docker compose ps api-server
echo ""

echo "2️⃣ API 服务器日志（最近 50 行）..."
docker compose logs api-server --tail 50
echo ""

echo "3️⃣ 检查容器内进程..."
docker compose exec api-server ps aux 2>&1 | head -10 || echo "无法检查进程"
echo ""

echo "4️⃣ 检查端口监听..."
docker compose exec api-server netstat -tlnp 2>&1 | grep 8028 || \
docker compose exec api-server ss -tlnp 2>&1 | grep 8028 || \
echo "无法检查端口，尝试其他方法..."
echo ""

echo "5️⃣ 测试容器内部连接..."
docker compose exec api-server curl -s http://localhost:8028/api/docs 2>&1 | head -5 || echo "容器内部无法连接"
echo ""

echo "6️⃣ 检查容器启动时间..."
docker compose ps api-server | grep api-server
echo ""

echo "✅ 诊断完成！"
echo ""
echo "📋 如果看到错误："
echo "   - 'ModuleNotFoundError': 需要重新构建镜像"
echo "   - 'Worker failed to boot': 查看完整日志"
echo "   - 容器不断重启: 检查启动命令"

