"""
转录组智能体（RNA Agent）
处理单细胞转录组（scRNA-seq）和 Bulk RNA-seq 分析
重构自现有的 BioBlendAgent
"""
import json
import os
from typing import Dict, Any, List, Optional, AsyncIterator
from ..base_agent import BaseAgent
from ...core.llm_client import LLMClient
from ...core.prompt_manager import PromptManager
from ...core.dispatcher import TaskDispatcher
from ...tools.cellranger_tool import CellRangerTool
from ...tools.scanpy_tool import ScanpyTool


class RNAAgent(BaseAgent):
    """
    转录组智能体
    
    职责：
    1. 处理单细胞转录组分析（scRNA-seq）
    2. 处理 Bulk RNA-seq 分析
    3. 生成工作流脚本
    4. 通过 TaskDispatcher 提交任务
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        prompt_manager: PromptManager,
        dispatcher: Optional[TaskDispatcher] = None,
        cellranger_config: Optional[Dict[str, Any]] = None,
        scanpy_config: Optional[Dict[str, Any]] = None
    ):
        """初始化转录组智能体"""
        super().__init__(llm_client, prompt_manager, "rna_expert")
        
        self.dispatcher = dispatcher
        self.cellranger_config = cellranger_config or {}
        self.scanpy_config = scanpy_config or {}
        self.cellranger_tool = CellRangerTool(self.cellranger_config)
        self.scanpy_tool = ScanpyTool(self.scanpy_config)
        
        # 标准工作流步骤（十步流程）
        self.workflow_steps = [
            {"name": "1. Quality Control", "tool_id": "local_qc", "desc": "过滤低质量细胞和基因"},
            {"name": "2. Normalization", "tool_id": "local_normalize", "desc": "数据标准化"},
            {"name": "3. Find Variable Genes", "tool_id": "local_hvg", "desc": "筛选高变基因"},
            {"name": "4. Scale Data", "tool_id": "local_scale", "desc": "数据缩放"},
            {"name": "5. PCA", "tool_id": "local_pca", "desc": "主成分分析"},
            {"name": "6. Compute Neighbors", "tool_id": "local_neighbors", "desc": "构建邻接图"},
            {"name": "7. Clustering", "tool_id": "local_cluster", "desc": "Leiden 聚类"},
            {"name": "8. UMAP Visualization", "tool_id": "local_umap", "desc": "UMAP 可视化"},
            {"name": "9. t-SNE Visualization", "tool_id": "local_tsne", "desc": "t-SNE 可视化"},
            {"name": "10. Find Markers", "tool_id": "local_markers", "desc": "寻找 Marker 基因"},
        ]
    
    async def process_query(
        self,
        query: str,
        history: List[Dict[str, str]] = None,
        uploaded_files: List[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        处理用户查询
        
        Returns:
            处理结果字典，可能包含：
            - workflow_config: 工作流配置（JSON）
            - chat_response: 聊天响应（流式）
            - task_submitted: 任务提交信息
        """
        query_lower = query.lower().strip()
        file_paths = self.get_file_paths(uploaded_files or [])
        
        # 意图识别
        is_workflow_request = self._is_workflow_request(query_lower, file_paths)
        
        if is_workflow_request:
            return await self._generate_workflow_config(query, file_paths)
        else:
            # 普通聊天
            return {
                "type": "chat",
                "response": self._stream_chat_response(query, file_paths)
            }
    
    def _is_workflow_request(self, query: str, file_paths: List[str]) -> bool:
        """判断是否是工作流请求"""
        workflow_keywords = [
            "规划", "流程", "workflow", "pipeline", "分析", "run",
            "执行", "plan", "做一下", "跑一下", "分析一下"
        ]
        
        bio_keywords = [
            "pca", "umap", "tsne", "qc", "质控", "聚类", "cluster"
        ]
        
        if any(kw in query for kw in workflow_keywords):
            return True
        
        if file_paths and any(kw in query for kw in bio_keywords):
            return True
        
        if file_paths and (not query or len(query) < 5):
            return True
        
        return False
    
    async def _generate_workflow_config(
        self,
        query: str,
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """生成工作流配置"""
        # 使用 LLM 提取参数
        extracted_params = await self._extract_workflow_params(query, file_paths)
        
        # 构建工作流配置
        workflow_config = {
            "workflow_name": "Standard Single-Cell Pipeline",
            "steps": []
        }
        
        for step_template in self.workflow_steps:
            step = step_template.copy()
            
            # 注入参数
            tool_id = step["tool_id"]
            if tool_id == "local_qc":
                step["params"] = {
                    "min_genes": extracted_params.get("min_genes", "200"),
                    "max_mt": extracted_params.get("max_mt", "20")
                }
            elif tool_id == "local_hvg":
                step["params"] = {
                    "n_top_genes": extracted_params.get("n_top_genes", "2000")
                }
            elif tool_id == "local_cluster":
                step["params"] = {
                    "resolution": extracted_params.get("resolution", "0.5")
                }
            else:
                step["params"] = {}
            
            workflow_config["steps"].append(step)
        
        return {
            "type": "workflow_config",
            "workflow_data": workflow_config,
            "file_paths": file_paths
        }
    
    async def _extract_workflow_params(
        self,
        query: str,
        file_paths: List[str]
    ) -> Dict[str, Any]:
        """使用 LLM 提取工作流参数"""
        prompt = f"""Extract workflow parameters from user query:

Query: {query}
Files: {', '.join(file_paths) if file_paths else 'None'}

Extract these parameters (if mentioned):
- min_genes (default: 200)
- max_mt (default: 20)
- resolution (default: 0.5)
- n_top_genes (default: 2000)

Return JSON only:
{{"resolution": "0.8", "min_genes": "500"}}
"""
        
        messages = [
            {"role": "system", "content": "You are a parameter extraction assistant. Return JSON only."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            completion = await self.llm_client.achat(messages, temperature=0.1, max_tokens=256)
            # 提取 think 过程和实际内容
            think_content, response = self.llm_client.extract_think_and_content(completion)
            # 如果有 think 内容，记录日志（可选）
            if think_content:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"RNA Agent think process: {think_content[:200]}...")
            
            # 解析 JSON
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            
            return json.loads(json_str)
        except:
            return {}
    
    async def _stream_chat_response(
        self,
        query: str,
        file_paths: List[str]
    ) -> AsyncIterator[str]:
        """流式聊天响应"""
        context = {
            "context": f"Uploaded files: {', '.join(file_paths) if file_paths else 'None'}"
        }
        
        async for chunk in self.chat(query, context, stream=True):
            yield chunk
    
    async def execute_workflow(
        self,
        workflow_config: Dict[str, Any],
        file_paths: List[str],
        output_dir: str
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        核心：直接执行 scanpy 分析流程（参考旧版本实现）
        
        Args:
            workflow_config: 工作流配置
            file_paths: 文件路径列表
            output_dir: 输出目录
        
        Returns:
            分析报告
        """
        # 检测输入文件类型
        input_path = file_paths[0] if file_paths else None
        if not input_path:
            raise ValueError("No input files provided")
        
        file_type = self.detect_file_type(input_path)
        
        # 设置输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 更新 scanpy 工具的输出目录
        self.scanpy_config["output_dir"] = output_dir
        # 重新初始化 scanpy 工具以使用新的输出目录
        self.scanpy_tool = ScanpyTool(self.scanpy_config)
        
        # 直接执行 Scanpy 流程
        if file_type == "fastq":
            # 需要先运行 Cell Ranger（暂不支持，先跳过）
            raise NotImplementedError("Cell Ranger preprocessing is not yet implemented")
        else:
            # 直接运行 Scanpy 分析
            steps = workflow_config.get("steps", [])
            
            # 执行分析流程
            report = self.scanpy_tool.run_pipeline(
                data_input=input_path,
                steps_config=steps
            )
            
            return report

