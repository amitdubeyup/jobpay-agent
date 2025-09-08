import os
from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "jobpay_agent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.matching_tasks",
        "app.workers.notification_tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "app.workers.matching_tasks.*": {"queue": "matching"},
    "app.workers.notification_tasks.*": {"queue": "notifications"},
}

# Retry configuration
celery_app.conf.task_annotations = {
    "*": {"rate_limit": "10/s"},
    "app.workers.matching_tasks.process_job_matching": {
        "rate_limit": "5/s",
        "time_limit": 600,  # 10 minutes
    },
    "app.workers.notification_tasks.send_notification_task": {
        "rate_limit": "20/s",
        "max_retries": 3,
    },
}

if __name__ == "__main__":
    celery_app.start()
