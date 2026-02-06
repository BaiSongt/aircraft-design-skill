from __future__ import annotations

from celery import Celery
from backend.config.app_config import settings

celery_app = Celery(
    "aircraft_design",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
)

# Auto-discover tasks if we have them in specific modules
# celery_app.autodiscover_tasks(['backend.services.calculation_service'])
