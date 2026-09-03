import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "discover-devices": {
        "task": "apps.monitoring.tasks.discover_devices",
        "schedule": crontab(minute="*/5"),
    },
    "check-device-status": {
        "task": "apps.monitoring.tasks.check_device_status",
        "schedule": crontab(minute="*"),
    },
    "sample-traffic": {
        "task": "apps.monitoring.tasks.sample_traffic",
        "schedule": 30.0,
    },
    "evaluate-alert-rules": {
        "task": "apps.monitoring.tasks.evaluate_alert_rules",
        "schedule": crontab(minute="*"),
    },
    "cleanup-old-traffic": {
        "task": "apps.monitoring.tasks.cleanup_old_traffic",
        "schedule": crontab(hour=2, minute=0),
    },
    "cleanup-old-telemetry": {
        "task": "apps.monitoring.tasks.cleanup_old_telemetry",
        "schedule": crontab(hour=2, minute=30),
    },
    "update-maintenance-windows": {
        "task": "apps.operations.tasks.update_maintenance_windows",
        "schedule": 30.0,
    },
}
