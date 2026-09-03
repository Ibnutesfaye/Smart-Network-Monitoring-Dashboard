from django.conf import settings
from django.db import models


class Report(models.Model):
    class ReportType(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    class ExportFormat(models.TextChoices):
        PDF = "pdf", "PDF"
        EXCEL = "excel", "Excel"
        CSV = "csv", "CSV"

    report_type = models.CharField(max_length=16, choices=ReportType.choices)
    export_format = models.CharField(max_length=8, choices=ExportFormat.choices, default=ExportFormat.PDF)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="reports"
    )
    file_path = models.CharField(max_length=512, blank=True)
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
