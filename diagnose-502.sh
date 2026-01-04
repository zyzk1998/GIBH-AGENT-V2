#!/bin/bash
# 502 错误诊断脚本

echo "🔍 GIBH-AGENT-V2 502 错误诊断"
echo "=================================="
echo ""

echo "1️⃣ 检查容器状态..."
docker compose ps
echo ""

echo "2️⃣ 检查 API 服务器日志（最近 50 行）..."
docker compose logs api-server --tail 50
echo ""

echo "3️⃣ 检查 Worker 日志（最近 30 行）..."
docker compose logs worker --tail 30
echo ""

echo "4️⃣ 检查 NGINX 日志（最近 20 行）..."
docker compose logs nginx --tail 20
echo ""

echo "5️⃣ 检查 API 服务器是否响应..."
docker compose exec api-server curl -s http://localhost:8000/api/docs 2>&1 | head -5 || echo "❌ API 服务器无响应"
echo ""

echo "6️⃣ 检查网络连接..."
docker compose exec nginx ping -c 2 api-server 2>&1 || echo "❌ NGINX 无法连接到 API 服务器"
echo ""

echo "✅ 诊断完成！"
echo ""
echo "📋 常见问题："
echo "   1. 如果看到 'ModuleNotFoundError: No module named paramiko'"
echo "      → 需要重新构建镜像：sudo ./docker-rebuild.sh"
echo ""
echo "   2. 如果看到 'Worker failed to boot'"
echo "      → 检查 requirements.txt 是否包含所有依赖"
echo ""
echo "   3. 如果容器不断重启"
echo "      → 查看完整日志：docker compose logs -f api-server"

