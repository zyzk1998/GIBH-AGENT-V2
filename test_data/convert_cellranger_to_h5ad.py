#!/usr/bin/env python3
"""
将 Cell Ranger 输出转换为 Scanpy 格式 (.h5ad)
"""

import scanpy as sc
import sys
import os

def convert_cellranger_to_h5ad(cellranger_output_dir, output_h5ad_path):
    """
    将 Cell Ranger 输出转换为 .h5ad 格式
    
    Args:
        cellranger_output_dir: Cell Ranger 输出目录 (包含 filtered_feature_bc_matrix)
        output_h5ad_path: 输出的 .h5ad 文件路径
    """
    print(f"📖 读取 Cell Ranger 输出: {cellranger_output_dir}")
    
    # 读取 Cell Ranger 输出
    adata = sc.read_10x_mtx(
        cellranger_output_dir,
        var_names='gene_symbols',  # 使用基因符号作为变量名
        cache=True
    )
    
    # 转置矩阵（Scanpy 使用 cells x genes 格式）
    adata.var_names_make_unique()
    
    print(f"✅ 数据加载成功:")
    print(f"   - 细胞数: {adata.n_obs:,}")
    print(f"   - 基因数: {adata.n_vars:,}")
    print(f"   - 矩阵类型: {type(adata.X)}")
    
    # 保存为 .h5ad 格式
    print(f"\n💾 保存为 .h5ad 格式: {output_h5ad_path}")
    adata.write(output_h5ad_path)
    
    print(f"✅ 转换完成！")
    print(f"   输出文件: {output_h5ad_path}")
    print(f"   文件大小: {os.path.getsize(output_h5ad_path) / 1024 / 1024:.2f} MB")
    
    return adata

if __name__ == "__main__":
    # 默认路径
    cellranger_matrix_dir = "/home/ubuntu/GIBH-AGENT-V2/test_data/pbmc_1k_v3_output/outs/filtered_feature_bc_matrix"
    output_h5ad = "/home/ubuntu/GIBH-AGENT-V2/test_data/pbmc_1k_v3_filtered.h5ad"
    
    # 如果提供了命令行参数，使用命令行参数
    if len(sys.argv) >= 2:
        cellranger_matrix_dir = sys.argv[1]
    if len(sys.argv) >= 3:
        output_h5ad = sys.argv[2]
    
    # 检查输入目录是否存在
    if not os.path.exists(cellranger_matrix_dir):
        print(f"❌ 错误: 输入目录不存在: {cellranger_matrix_dir}")
        sys.exit(1)
    
    # 执行转换
    adata = convert_cellranger_to_h5ad(cellranger_matrix_dir, output_h5ad)
    
    print("\n📊 数据预览:")
    print(adata)

