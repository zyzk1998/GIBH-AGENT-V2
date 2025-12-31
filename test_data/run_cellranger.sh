#!/bin/bash
# Cell Ranger 运行脚本

set -e  # 遇到错误立即退出

echo "🚀 开始运行 Cell Ranger count..."

# 进入测试数据目录
cd /home/ubuntu/GIBH-AGENT-V2/test_data

# 步骤 1: 解压参考基因组（如果未解压）
if [ ! -d "refdata-gex-GRCh38-2024-A" ]; then
    echo "📦 解压参考基因组（这可能需要几分钟）..."
    tar -xzf refdata-gex-GRCh38-2024-A.tar.gz
    echo "✅ 参考基因组解压完成"
else
    echo "✅ 参考基因组已存在"
fi

# 步骤 2: 检查 FASTQ 文件
if [ ! -d "pbmc_1k_v3_fastqs" ]; then
    echo "❌ 错误: FASTQ 文件目录不存在"
    exit 1
fi

echo "✅ FASTQ 文件检查通过"
echo "   FASTQ 文件数量: $(ls pbmc_1k_v3_fastqs/*.fastq.gz | wc -l)"

# 步骤 3: 运行 Cell Ranger count
echo ""
echo "🔬 开始运行 Cell Ranger count..."
echo "   样本: pbmc_1k_v3"
echo "   输出目录: pbmc_1k_v3_output"
echo ""

/home/ubuntu/cellranger-10.0.0/bin/cellranger count \
  --id=pbmc_1k_v3_output \
  --create-bam=false \
  --transcriptome=$(pwd)/refdata-gex-GRCh38-2024-A \
  --fastqs=$(pwd)/pbmc_1k_v3_fastqs \
  --sample=pbmc_1k_v3 \
  --localcores=8 \
  --localmem=32

# 步骤 4: 检查结果
if [ -d "pbmc_1k_v3_output" ]; then
    echo ""
    echo "✅ Cell Ranger 运行完成！"
    echo ""
    echo "📊 输出文件:"
    ls -lh pbmc_1k_v3_output/outs/ | head -10
    echo ""
    echo "📈 关键指标:"
    if [ -f "pbmc_1k_v3_output/outs/metrics_summary.csv" ]; then
        cat pbmc_1k_v3_output/outs/metrics_summary.csv
    fi
    echo ""
    echo "🌐 查看网页报告:"
    echo "   file://$(pwd)/pbmc_1k_v3_output/outs/web_summary.html"
else
    echo "❌ 错误: 输出目录未创建，运行可能失败"
    exit 1
fi
