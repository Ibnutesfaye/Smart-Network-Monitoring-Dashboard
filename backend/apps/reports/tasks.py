from celery import shared_task

from .models import Report
from .services.generator import generate_report_file


@shared_task
def generate_report_task(report_id):
    report = Report.objects.get(pk=report_id)
    generate_report_file(report)
    return report.id
