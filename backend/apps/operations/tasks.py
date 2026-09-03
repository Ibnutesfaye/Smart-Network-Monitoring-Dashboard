from celery import shared_task

from .services import evaluate_maintenance_windows


@shared_task
def update_maintenance_windows():
    return evaluate_maintenance_windows()
