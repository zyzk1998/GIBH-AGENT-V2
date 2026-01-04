"""
Celery 异步任务定义
"""
import logging
from pathlib import Path
from typing import Dict, Any, List
from gibh_agent.core.celery_app import celery_app
from gibh_agent import create_agent

logger = logging.getLogger(__name__)

# 全局智能体实例（延迟初始化）
_agent = None

def get_agent():
    """获取或创建智能体实例（单例模式）"""
    global _agent
    if _agent is None:
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        _agent = create_agent(str(config_path))
        logger.info("✅ Celery Worker: 智能体初始化成功")
    return _agent

@celery_app.task(name="gibh_agent.execute_workflow", bind=True)
def execute_workflow_task(self, workflow_config: Dict[str, Any], file_paths: List[str], output_dir: str) -> Dict[str, Any]:
    """
    异步执行工作流任务
    
    Args:
        workflow_config: 工作流配置
        file_paths: 文件路径列表
        output_dir: 输出目录
    
    Returns:
        执行结果
    """
    try:
        logger.info(f"🚀 Celery Worker: 开始执行工作流任务 {self.request.id}")
        logger.info(f"📁 文件路径: {file_paths}")
        logger.info(f"📂 输出目录: {output_dir}")
        
        # 获取智能体
        agent = get_agent()
        
        # 获取 RNA Agent
        rna_agent = agent.agents.get("rna_agent")
        if not rna_agent:
            raise ValueError("RNA Agent 未找到")
        
        # 执行工作流（同步调用，因为已经在 Celery Worker 中）
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                rna_agent.execute_workflow(
                    workflow_config=workflow_config,
                    file_paths=file_paths,
                    output_dir=output_dir
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Celery Worker: 工作流执行失败: {e}", exc_info=True)
        raise

@celery_app.task(name="gibh_agent.process_query", bind=True)
def process_query_task(self, query: str, history: List[Dict[str, str]] = None, uploaded_files: List[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
    """
    异步处理用户查询任务
    
    Args:
        query: 用户查询
        history: 对话历史
        uploaded_files: 上传的文件列表
        **kwargs: 其他参数
    
    Returns:
        处理结果
    """
    try:
        logger.info(f"💬 Celery Worker: 开始处理查询任务 {self.request.id}")
        logger.info(f"📝 查询内容: {query[:100]}...")
        
        # 获取智能体
        agent = get_agent()
        
        # 处理查询（同步调用）
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                agent.process_query(
                    query=query,
                    history=history or [],
                    uploaded_files=uploaded_files or [],
                    **kwargs
                )
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"❌ Celery Worker: 查询处理失败: {e}", exc_info=True)
        raise

