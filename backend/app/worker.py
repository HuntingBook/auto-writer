from celery import Celery

from app.core.config import settings


celery_app = Celery(
  "auto_writer",
  broker=settings.redis_url,
  backend=settings.redis_url,
  include=["app.workers.novel_tasks"],
)

celery_app.conf.update(
  task_track_started=True,
  timezone="UTC",
)
