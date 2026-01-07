"""
文件检测器
主动分析上传的文件，生成元数据，避免 Agent 读取大文件
"""
import os
import json
import gzip
from pathlib import Path
from typing import Dict, Optional


class FileInspector:
    """文件检测器，用于主动生成文件元数据"""
    
    def __init__(self, upload_dir: str):
        """
        初始化文件检测器
        
        Args:
            upload_dir: 上传文件目录
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _is_gzipped(self, filepath: Path) -> bool:
        """检查文件是否为 gzip 压缩"""
        # 🔥 Task 2: Check if path is directory before trying to open
        if filepath.is_dir():
            return False
        try:
            with open(filepath, 'rb') as f:
                return f.read(2) == b'\x1f\x8b'
        except:
            return False
    
    def _read_head(self, filepath: Path, lines: int = 5) -> list:
        """安全读取文件前几行"""
        # 🔥 Task 2: Check if path is directory before trying to open
        if filepath.is_dir():
            return []
        try:
            if self._is_gzipped(filepath):
                with gzip.open(filepath, 'rt') as f:
                    return [next(f).strip() for _ in range(lines) if True]
            else:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return [next(f).strip() for _ in range(lines) if True]
        except Exception:
            return []
    
    def generate_metadata(self, filename: str) -> Optional[Dict]:
        """
        主动检测：分析单个文件并保存 .meta.json
        
        Args:
            filename: 文件名或目录名
        
        Returns:
            元数据字典，如果失败返回 None
        """
        filepath = self.upload_dir / filename
        if not filepath.exists():
            return None
        
        # 🔥 Task 2: Handle directory paths (10x Genomics format)
        if filepath.is_dir():
            # Check if it's a 10x directory (contains matrix.mtx, etc.)
            try:
                dir_contents = os.listdir(filepath)
                if any(f in dir_contents for f in ['matrix.mtx', 'matrix.mtx.gz']):
                    meta = {
                        "filename": filename,
                        "file_type": "10x_genomics",
                        "path": str(filepath),
                        "files": dir_contents,
                        "is_directory": True
                    }
                    # Save metadata
                    meta_path = filepath / '.meta.json'
                    try:
                        with open(meta_path, 'w', encoding='utf-8') as f:
                            json.dump(meta, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        print(f"⚠️ 保存目录元数据失败: {e}")
                    return meta
                else:
                    # Unknown directory format
                    return {
                        "filename": filename,
                        "file_type": "directory",
                        "error": "Unknown directory format",
                        "is_directory": True
                    }
            except Exception as e:
                print(f"⚠️ 检查目录失败: {e}")
                return None
        
        meta = {
            "filename": filename,
            "size_bytes": filepath.stat().st_size,
            "size_mb": round(filepath.stat().st_size / (1024 * 1024), 2),
            "file_type": "unknown",
            "estimated_cells": "unknown",
            "estimated_genes": "unknown"
        }
        
        # 单细胞 H5AD
        if filename.endswith('.h5ad'):
            meta["file_type"] = "h5ad"
            # 根据文件大小估算细胞数
            if meta["size_mb"] > 500:
                meta["estimated_cells"] = ">10k"
            elif meta["size_mb"] > 100:
                meta["estimated_cells"] = "5k-10k"
            else:
                meta["estimated_cells"] = "<5k"
            meta["estimated_genes"] = ">20k"
        
        # 单细胞 Matrix
        elif "matrix" in filename.lower() and (".mtx" in filename.lower() or ".mtx.gz" in filename.lower()):
            meta["file_type"] = "matrix"
            head = self._read_head(filepath, 3)
            for line in head:
                if not line.startswith('%'):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            rows = int(parts[0])
                            cols = int(parts[1])
                            meta["estimated_genes"] = rows
                            meta["estimated_cells"] = cols
                        except:
                            pass
                    break
        
        # FASTQ 文件
        elif filename.endswith(('.fastq', '.fq', '.fastq.gz', '.fq.gz')):
            meta["file_type"] = "fastq"
            # FASTQ 文件通常很大，无法准确估算
        
        # CSV 文件（代谢组学等）
        elif filename.endswith('.csv'):
            meta["file_type"] = "csv"
            head = self._read_head(filepath, 1)
            if head:
                # 估算列数（假设第一行是表头）
                meta["estimated_genes"] = len(head[0].split(','))
        
        # TSV 文件
        elif filename.endswith('.tsv'):
            meta["file_type"] = "tsv"
            head = self._read_head(filepath, 1)
            if head:
                meta["estimated_genes"] = len(head[0].split('\t'))
        
        # 保存元数据
        meta_path = filepath.with_suffix(filepath.suffix + '.meta.json')
        try:
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存元数据失败: {e}")
        
        return meta
    
    def get_metadata(self, filename: str) -> Optional[Dict]:
        """
        获取文件的元数据（如果已生成）
        
        Args:
            filename: 文件名
        
        Returns:
            元数据字典，如果不存在返回 None
        """
        filepath = self.upload_dir / filename
        meta_path = filepath.with_suffix(filepath.suffix + '.meta.json')
        
        if meta_path.exists():
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        return None

