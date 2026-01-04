"""
GIBH-AGENT 主入口
整合所有组件：路由智能体 + 领域智能体
"""
import os
import re
import yaml
import logging
from typing import Dict, Any, Optional
from .core.llm_client import LLMClient, LLMClientFactory
from .core.prompt_manager import PromptManager, create_default_prompt_manager
from .core.dispatcher import TaskDispatcher, create_dispatcher_from_config
from .agents.router_agent import RouterAgent
from .agents.base_agent import BaseAgent
from .agents.specialists.rna_agent import RNAAgent
from .agents.specialists.dna_agent import DNAAgent
from .agents.specialists.epigenomics_agent import EpigenomicsAgent
from .agents.specialists.metabolomics_agent import MetabolomicsAgent
from .agents.specialists.proteomics_agent import ProteomicsAgent
from .agents.specialists.spatial_agent import SpatialAgent
from .agents.specialists.imaging_agent import ImagingAgent

logger = logging.getLogger(__name__)


class GIBHAgent:
    """
    GIBH-AGENT 主类
    
    整合路由智能体和所有领域智能体
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        初始化 GIBH-AGENT
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化核心组件
        self.llm_clients = self._init_llm_clients()
        self.prompt_manager = self._init_prompt_manager()
        self.dispatcher = self._init_dispatcher()
        
        # 初始化路由智能体
        self.router = RouterAgent(
            llm_client=self.llm_clients["logic"],
            prompt_manager=self.prompt_manager
        )
        
        # 初始化领域智能体
        self.agents = self._init_domain_agents()
    
    def _substitute_env_vars(self, value: Any) -> Any:
        """
        递归替换配置中的环境变量
        支持格式: ${VAR:default} 或 ${VAR}
        """
        if isinstance(value, str):
            # 匹配 ${VAR:default} 或 ${VAR} 格式
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
            
            def replace_match(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) is not None else ""
                env_value = os.getenv(var_name, default_value)
                return env_value
            
            return re.sub(pattern, replace_match, value)
        elif isinstance(value, dict):
            return {k: self._substitute_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._substitute_env_vars(item) for item in value]
        else:
            return value
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件并替换环境变量"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # 替换环境变量
                config = self._substitute_env_vars(config)
                return config
        return {}
    
    def _init_llm_clients(self) -> Dict[str, LLMClient]:
        """初始化 LLM 客户端"""
        llm_config = self.config.get("llm", {})
        default_type = llm_config.get("default", "cloud")
        
        clients = {}
        
        if default_type == "local":
            local_config = llm_config.get("local", {})
            clients["logic"] = LLMClientFactory.create_from_config(local_config.get("logic", {}))
            clients["vision"] = LLMClientFactory.create_from_config(local_config.get("vision", {}))
        else:
            # 默认使用硅基流动 deepseek API
            cloud_config = llm_config.get("cloud", {})
            siliconflow_config = cloud_config.get("siliconflow", {})
            if siliconflow_config:
                # 验证 API 密钥
                api_key = siliconflow_config.get("api_key", "")
                if not api_key or api_key.strip() == "":
                    error_msg = (
                        "❌ API 密钥未设置！\n"
                        "请设置环境变量 SILICONFLOW_API_KEY:\n"
                        "  export SILICONFLOW_API_KEY='your_api_key_here'\n"
                        "或者在配置文件中直接设置 api_key 字段。"
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                clients["logic"] = LLMClientFactory.create_from_config(siliconflow_config)
                clients["vision"] = LLMClientFactory.create_from_config(siliconflow_config)
            else:
                # 回退到工厂方法
                api_key = os.getenv("SILICONFLOW_API_KEY", "")
                if not api_key or api_key.strip() == "":
                    error_msg = (
                        "❌ API 密钥未设置！\n"
                        "请设置环境变量 SILICONFLOW_API_KEY:\n"
                        "  export SILICONFLOW_API_KEY='your_api_key_here'"
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                clients["logic"] = LLMClientFactory.create_cloud_siliconflow()
                clients["vision"] = LLMClientFactory.create_cloud_siliconflow()
        
        return clients
    
    def _init_prompt_manager(self) -> PromptManager:
        """初始化提示管理器"""
        template_dir = os.path.join(os.path.dirname(__file__), "..", "config", "prompts")
        if os.path.exists(template_dir):
            return PromptManager(template_dir)
        return create_default_prompt_manager()
    
    def _init_dispatcher(self) -> Optional[TaskDispatcher]:
        """初始化任务分发器"""
        dispatcher_config = self.config.get("dispatcher", {})
        if dispatcher_config:
            return TaskDispatcher(dispatcher_config)
        return None
    
    def _init_domain_agents(self) -> Dict[str, BaseAgent]:
        """初始化所有领域智能体"""
        agents = {}
        
        # RNA Agent（转录组）
        test_data_dir = self.config.get("tools", {}).get("test_data_dir", None)
        agents["rna_agent"] = RNAAgent(
            llm_client=self.llm_clients["logic"],
            prompt_manager=self.prompt_manager,
            dispatcher=self.dispatcher,
            cellranger_config=self.config.get("tools", {}).get("cellranger", {}),
            scanpy_config=self.config.get("tools", {}).get("scanpy", {}),
            test_data_dir=test_data_dir
        )
        
        # DNA Agent（基因组）
        agents["dna_agent"] = DNAAgent(
            llm_client=self.llm_clients["logic"],
            prompt_manager=self.prompt_manager
        )
        
        # 其他智能体（占位符）
        agents["epigenomics_agent"] = EpigenomicsAgent(
            llm_client=self.llm_clients["logic"],
            prompt_manager=self.prompt_manager
        )
        
        agents["metabolomics_agent"] = MetabolomicsAgent(
            llm_client=self.llm_clients["logic"],
            prompt_manager=self.prompt_manager,
            metabolomics_config=self.config.get("tools", {}).get("metabolomics", {})
        )
        
        agents["proteomics_agent"] = ProteomicsAgent(
            llm_client=self.llm_clients["logic"],
            prompt_manager=self.prompt_manager
        )
        
        agents["spatial_agent"] = SpatialAgent(
            llm_client=self.llm_clients["logic"],
            prompt_manager=self.prompt_manager
        )
        
        agents["imaging_agent"] = ImagingAgent(
            llm_client=self.llm_clients["logic"],
            prompt_manager=self.prompt_manager
        )
        
        return agents
    
    async def process_query(
        self,
        query: str,
        history: list = None,
        uploaded_files: list = None,
        **kwargs
    ):
        """
        处理用户查询（主入口）
        
        Args:
            query: 用户查询文本
            history: 对话历史
            uploaded_files: 上传的文件列表
            **kwargs: 其他参数（如 test_dataset_id）将传递给目标智能体
        
        Returns:
            处理结果（可能是字典或异步生成器）
        """
        try:
            # 1. 路由到对应的领域智能体
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔀 开始路由决策: 查询='{query[:50]}...', 文件数={len(uploaded_files or [])}")
            
            route_result = await self.router.process_query(query, history, uploaded_files)
            
            logger.info(f"✅ 路由完成: {route_result.get('routing')} (modality: {route_result.get('modality')}, confidence: {route_result.get('confidence', 0):.2f})")
            
            # 2. 获取目标智能体
            routing = route_result.get("routing", "rna_agent")
            target_agent = self.agents.get(routing)
            
            # 如果路由的智能体不存在，使用默认的 RNA Agent
            if not target_agent:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"路由的智能体不存在: {routing}，使用默认 rna_agent")
                target_agent = self.agents.get("rna_agent")
            
            if not target_agent:
                raise ValueError("RNA Agent 未初始化")
            
            # 3. 处理查询（传递所有 kwargs 给目标智能体）
            result = await target_agent.process_query(query, history, uploaded_files, **kwargs)
            
            # 4. 添加路由信息
            result["routing_info"] = route_result
            
            return result
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"处理查询失败: {e}", exc_info=True)
            # 返回错误信息而不是抛出异常
            return {
                "type": "error",
                "error": str(e),
                "message": f"处理失败: {str(e)}"
            }


# 便捷函数
def create_agent(config_path: str = "config/settings.yaml") -> GIBHAgent:
    """创建 GIBH-AGENT 实例"""
    return GIBHAgent(config_path)


if __name__ == "__main__":
    # 示例使用
    import asyncio
    
    async def main():
        agent = create_agent()
        
        # 测试路由
        result = await agent.process_query(
            query="帮我分析一下这个单细胞数据",
            uploaded_files=[{"name": "sample.h5ad", "path": "/data/sample.h5ad"}]
        )
        
        print("Routing result:", result.get("routing_info"))
        print("Agent response:", result)
    
    asyncio.run(main())

