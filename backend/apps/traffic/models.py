from django.db import models

from apps.devices.models import Device


class TrafficSample(models.Model):
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="traffic_samples", null=True, blank=True
    )
    upload_speed = models.FloatField(help_text="Mbps")
    download_speed = models.FloatField(help_text="Mbps")
    bandwidth_usage = models.FloatField(help_text="Total Mbps")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["device", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]
