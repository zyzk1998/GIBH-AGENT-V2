"""
server.py 的 Celery 集成示例
展示如何将工作流执行改为异步任务

注意：这是一个示例文件，不会影响当前的 server.py
如果需要使用 Celery，可以按照这个示例修改 server.py
"""
from gibh_agent.core.tasks import execute_workflow_task, process_query_task
from fastapi.responses import JSONResponse
from datetime import datetime

# =========================================
# 示例 1: 异步执行工作流
# =========================================
@app.post("/api/execute-async")
async def execute_workflow_async(request: dict):
    """
    异步执行工作流（使用 Celery）
    
    返回任务 ID，客户端需要轮询或使用 WebSocket 获取结果
    """
    if not agent:
        raise HTTPException(status_code=500, detail="智能体未初始化")
    
    try:
        workflow_data = request.get("workflow_data")
        file_paths = request.get("file_paths", [])
        output_dir = str(RESULTS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        logger.info(f"🚀 提交异步工作流任务: {len(file_paths)} 个文件")
        
        # 提交到 Celery
        task = execute_workflow_task.delay(
            workflow_config=workflow_data,
            file_paths=file_paths,
            output_dir=output_dir
        )
        
        return JSONResponse(content={
            "status": "submitted",
            "task_id": task.id,
            "message": "任务已提交，正在处理中...",
            "check_status_url": f"/api/task/{task.id}/status"
        })
        
    except Exception as e:
        logger.error(f"❌ 任务提交失败: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )

# =========================================
# 示例 2: 查询任务状态
# =========================================
@app.get("/api/task/{task_id}/status")
async def get_task_status(task_id: str):
    """
    查询 Celery 任务状态
    """
    from celery.result import AsyncResult
    from gibh_agent.core.celery_app import celery_app
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == "PENDING":
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "status": "任务等待中..."
        }
    elif task_result.state == "PROGRESS":
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "status": "任务执行中...",
            "progress": task_result.info.get("progress", 0) if isinstance(task_result.info, dict) else None
        }
    elif task_result.state == "SUCCESS":
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "status": "任务完成",
            "result": task_result.result
        }
    else:  # FAILURE
        response = {
            "task_id": task_id,
            "state": task_result.state,
            "status": "任务失败",
            "error": str(task_result.info) if task_result.info else "未知错误"
        }
    
    return JSONResponse(content=response)

# =========================================
# 示例 3: 异步处理查询（可选）
# =========================================
@app.post("/api/chat-async")
async def chat_async(req: ChatRequest):
    """
    异步处理用户查询（适用于复杂查询）
    """
    if not agent:
        raise HTTPException(status_code=500, detail="智能体未初始化")
    
    try:
        # 提交到 Celery
        task = process_query_task.delay(
            query=req.message,
            history=req.history or [],
            uploaded_files=req.uploaded_files or [],
            test_dataset_id=req.test_dataset_id
        )
        
        return JSONResponse(content={
            "status": "submitted",
            "task_id": task.id,
            "message": "查询已提交，正在处理中...",
            "check_status_url": f"/api/task/{task.id}/status"
        })
        
    except Exception as e:
        logger.error(f"❌ 查询提交失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

