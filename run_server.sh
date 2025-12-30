#!/bin/bash
# 启动测试服务器脚本

echo "🚀 启动 GIBH-AGENT-V2 测试服务器..."

# 检查环境变量
if [ -z "$SILICONFLOW_API_KEY" ]; then
    echo "⚠️  警告: 未设置 SILICONFLOW_API_KEY 环境变量"
    echo "   请设置: export SILICONFLOW_API_KEY='your_api_key'"
fi

# 创建必要的目录
mkdir -p uploads results

# 启动服务器
python server.py

