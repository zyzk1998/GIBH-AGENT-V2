# Cell Ranger 10.0.0 运行教程

## 📋 准备工作检查

### 1. 数据文件
- ✅ FASTQ 文件：`/home/ubuntu/GIBH-AGENT-V2/test_data/pbmc_1k_v3_fastqs/`
  - 包含 2 个 lane (L001, L002)
  - 每个 lane 有 I1 (index), R1 (read1), R2 (read2) 文件

### 2. 参考基因组
- ⚠️ 需要解压：`refdata-gex-GRCh38-2024-A.tar.gz` (11G)

### 3. Cell Ranger
- ✅ 已安装：`/home/ubuntu/cellranger-10.0.0` (版本 10.0.0)

## 🚀 运行步骤

### 步骤 1: 解压参考基因组

```bash
cd /home/ubuntu/GIBH-AGENT-V2/test_data

# 解压参考基因组（需要一些时间，约 11GB）
tar -xzf refdata-gex-GRCh38-2024-A.tar.gz

# 验证解压结果
ls -lh refdata-gex-GRCh38-2024-A/
# 应该看到：fasta/, genes/, reference.json 等文件
```

### 步骤 2: 准备 FASTQ 文件

FASTQ 文件已经在正确的位置：
```
/home/ubuntu/GIBH-AGENT-V2/test_data/pbmc_1k_v3_fastqs/
├── pbmc_1k_v3_S1_L001_I1_001.fastq.gz
├── pbmc_1k_v3_S1_L001_R1_001.fastq.gz
├── pbmc_1k_v3_S1_L001_R2_001.fastq.gz
├── pbmc_1k_v3_S1_L002_I1_001.fastq.gz
├── pbmc_1k_v3_S1_L002_R1_001.fastq.gz
└── pbmc_1k_v3_S1_L002_R2_001.fastq.gz
```

### 步骤 3: 运行 Cell Ranger count

```bash
cd /home/ubuntu/GIBH-AGENT-V2/test_data

# 设置 Cell Ranger 路径（可选，如果已添加到 PATH）
export PATH=/home/ubuntu/cellranger-10.0.0:$PATH

# 运行 cellranger count
/home/ubuntu/cellranger-10.0.0/bin/cellranger count \
  --id=pbmc_1k_v3_output \
  --create-bam=false \
  --transcriptome=/home/ubuntu/GIBH-AGENT-V2/test_data/refdata-gex-GRCh38-2024-A \
  --fastqs=/home/ubuntu/GIBH-AGENT-V2/test_data/pbmc_1k_v3_fastqs \
  --sample=pbmc_1k_v3 \
  --localcores=8 \
  --localmem=32
```

### 参数说明

- `--id`: 输出目录名称（会在当前目录创建）
- `--create-bam`: 是否创建 BAM 文件（false=不创建，节省空间和时间；true=创建，用于后续分析）
- `--transcriptome`: 参考基因组路径（解压后的目录）
- `--fastqs`: FASTQ 文件所在目录
- `--sample`: 样本名称（从 FASTQ 文件名中提取，格式：`{sample}_S1_L001_R1_001.fastq.gz`）
- `--localcores`: 使用的 CPU 核心数（根据服务器调整）
- `--localmem`: 使用的内存（GB，根据服务器调整）

### 步骤 4: 检查运行结果

运行完成后，检查输出：

```bash
# 查看输出目录
ls -lh pbmc_1k_v3_output/

# 查看主要输出文件
ls -lh pbmc_1k_v3_output/outs/

# 检查 web_summary.html（在浏览器中打开查看）
# 检查 metrics_summary.csv（关键指标）
cat pbmc_1k_v3_output/outs/metrics_summary.csv

# 检查生成的 .h5ad 文件（如果生成）
find pbmc_1k_v3_output/ -name "*.h5ad"
```

## 📊 预期输出

运行成功后，`pbmc_1k_v3_output/outs/` 目录应包含：

- `web_summary.html` - 网页摘要报告
- `metrics_summary.csv` - 指标摘要
- `molecule_info.h5` - 分子信息
- `filtered_feature_bc_matrix/` - 过滤后的特征-条形码矩阵
- `raw_feature_bc_matrix/` - 原始特征-条形码矩阵
- `cloupe.cloupe` - Loupe 浏览器文件（可选）

## ⚠️ 注意事项

1. **内存要求**: Cell Ranger 需要大量内存，建议至少 32GB
2. **运行时间**: 1k 细胞的数据集通常需要 10-30 分钟
3. **磁盘空间**: 确保有足够的磁盘空间（至少 20GB 可用空间）
4. **样本名称**: 确保 FASTQ 文件名格式正确，Cell Ranger 会自动识别

## 🔍 故障排查

### 问题 1: 找不到参考基因组
```bash
# 检查路径是否正确
ls -lh /home/ubuntu/GIBH-AGENT-V2/test_data/refdata-gex-GRCh38-2024-A/
```

### 问题 2: 样本名称识别错误
```bash
# 检查 FASTQ 文件名格式
ls pbmc_1k_v3_fastqs/
# 格式应为: {sample}_S{sample_number}_L{lane}_{read_type}_{chunk}.fastq.gz
```

### 问题 3: 内存不足
```bash
# 减少使用的内存和核心数
--localcores=4 --localmem=16
```

## 📝 快速命令（一键运行）

```bash
cd /home/ubuntu/GIBH-AGENT-V2/test_data

# 1. 解压参考基因组（如果未解压）
[ ! -d "refdata-gex-GRCh38-2024-A" ] && tar -xzf refdata-gex-GRCh38-2024-A.tar.gz

# 2. 运行 Cell Ranger
/home/ubuntu/cellranger-10.0.0/bin/cellranger count \
  --id=pbmc_1k_v3_output \
  --create-bam=false \
  --transcriptome=$(pwd)/refdata-gex-GRCh38-2024-A \
  --fastqs=$(pwd)/pbmc_1k_v3_fastqs \
  --sample=pbmc_1k_v3 \
  --localcores=8 \
  --localmem=32

# 3. 检查结果
echo "✅ 运行完成！输出目录: pbmc_1k_v3_output/"
ls -lh pbmc_1k_v3_output/outs/ | head -10
```

