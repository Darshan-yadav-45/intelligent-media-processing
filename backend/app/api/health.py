"""
Health check endpoint: reports DB, Redis, and Celery worker availability.
"""
import logging
from fastapi import APIRouter
from sqlalchemy import text
import redis as redis_lib

from app.database import SessionLocal
from app.config import get_settings
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    result = {"status": "healthy", "database": "unknown", "redis": "unknown", "worker": "unknown"}

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        result["database"] = "connected"
    except Exception as exc:
        logger.error("Health check DB failure: %s", exc)
        result["database"] = "unavailable"
        result["status"] = "degraded"

    try:
        client = redis_lib.Redis(host=settings.redis_host, port=settings.redis_port, socket_connect_timeout=2)
        client.ping()
        result["redis"] = "connected"
    except Exception as exc:
        logger.error("Health check Redis failure: %s", exc)
        result["redis"] = "unavailable"
        result["status"] = "degraded"

    try:
        stats = celery_app.control.inspect(timeout=2).stats()
        result["worker"] = "available" if stats else "unavailable"
        if not stats:
            result["status"] = "degraded"
    except Exception as exc:
        logger.error("Health check worker failure: %s", exc)
        result["worker"] = "unavailable"
        result["status"] = "degraded"

    return result
