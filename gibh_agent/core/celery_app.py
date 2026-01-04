"""
Celery 任务配置
用于异步执行耗时的生信分析任务
"""
import os
from celery import Celery
from pathlib import Path

# 从环境变量获取 Redis URL
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 创建 Celery 应用
celery_app = Celery(
    "gibh_agent",
    broker=redis_url,
    backend=redis_url,
    include=["gibh_agent.core.tasks"]
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 小时超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

# 自动发现任务
celery_app.autodiscover_tasks(["gibh_agent.core"])

