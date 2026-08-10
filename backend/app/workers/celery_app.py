"""
Celery application instance and configuration.
Run the worker with:
    celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
"""
from celery import Celery
from app.models import User, Image, ImageStatus, ProcessingJob, AnalysisResult
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "media_pipeline",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,          # re-queue task if worker dies mid-processing
    worker_prefetch_multiplier=1,  # avoids one worker hoarding jobs -> fairer concurrency
    task_reject_on_worker_lost=True,
)
