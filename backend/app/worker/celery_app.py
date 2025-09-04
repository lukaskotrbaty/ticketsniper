from celery import Celery
from app.core.config import settings # Assuming settings are accessible from worker

# Use the project name for the Celery app instance, or choose a specific name
# Ensure this name matches how you refer to the app in commands (e.g., celery -A app.worker.celery_app ...)
# The first argument is typically the name of the current module.
celery_app = Celery("worker")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
# We are configuring directly here instead of using a namespace.
celery_app.conf.update(
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Europe/Prague',
    enable_utc=True,
    include=['app.worker.tasks']
)

celery_app.conf.beat_schedule = {
    'schedule-route-checks-every-x-seconds': {
        'task': 'app.worker.tasks.schedule_route_checks',
        'schedule': settings.ROUTE_AVAILABILITY_CHECK_SCHEDULE_INTERVAL_SECONDS
    },
    'expire-past-routes-every-5-minutes': {
        'task': 'app.worker.tasks.expire_past_routes',
        'schedule': settings.ROUTE_EXPIRATION_CHECK_SCHEDULE_INTERVAL_SECONDS
    },
}

if __name__ == '__main__':
    celery_app.start()
