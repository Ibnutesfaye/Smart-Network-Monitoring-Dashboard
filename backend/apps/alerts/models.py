from django.db import models

from apps.devices.models import Device
from apps.devices.models import Site
from django.conf import settings


class Alert(models.Model):
    class Level(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class AlertType(models.TextChoices):
        UNKNOWN_DEVICE = "unknown_device", "Unknown Device Detected"
        DEVICE_OFFLINE = "device_offline", "Device Offline"
        HIGH_BANDWIDTH = "high_bandwidth", "High Bandwidth Usage"
        SUSPICIOUS_ACTIVITY = "suspicious_activity", "Suspicious Activity"
        FAILED_ACCESS = "failed_access", "Repeated Failed Access Attempts"
        DEVICE_RECOVERED = "device_recovered", "Device Recovered"
        HIGH_LATENCY = "high_latency", "High Latency"
        PACKET_LOSS = "packet_loss", "Packet Loss"
        HIGH_CPU = "high_cpu", "High CPU"
        HIGH_MEMORY = "high_memory", "High Memory"
        INTERFACE_DOWN = "interface_down", "Interface Down"
        HIGH_INTERFACE_UTILIZATION = "high_interface_utilization", "High Interface Utilization"
        INTERFACE_ERRORS = "interface_errors", "Interface Errors"

    class State(models.TextChoices):
        PENDING = "pending", "Pending"
        FIRING = "firing", "Firing"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"

    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="alerts", null=True, blank=True
    )
    interface = models.ForeignKey("devices.DeviceInterface", on_delete=models.CASCADE, related_name="alerts", null=True, blank=True)
    alert_level = models.CharField(max_length=16, choices=Level.choices, db_index=True)
    alert_type = models.CharField(max_length=32, choices=AlertType.choices, db_index=True)
    message = models.TextField()
    acknowledged = models.BooleanField(default=False)
    state = models.CharField(max_length=16, choices=State.choices, default=State.FIRING, db_index=True)
    deduplication_key = models.CharField(max_length=255, blank=True, db_index=True)
    first_triggered_at = models.DateTimeField(null=True, blank=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    occurrence_count = models.PositiveIntegerField(default=1)
    recovery_count = models.PositiveIntegerField(default=0)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="acknowledged_alerts")
    acknowledgement_note = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    maintenance_suppressed = models.BooleanField(default=False, db_index=True)
    maintenance_window = models.ForeignKey("operations.MaintenanceWindow", null=True, blank=True, on_delete=models.SET_NULL, related_name="suppressed_alerts")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


class AlertRule(models.Model):
    name = models.CharField(max_length=128)
    alert_type = models.CharField(max_length=32, choices=Alert.AlertType.choices)
    alert_level = models.CharField(max_length=16, choices=Alert.Level.choices)
    bandwidth_threshold_mbps = models.FloatField(null=True, blank=True)
    offline_minutes = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    threshold = models.FloatField(null=True, blank=True)
    comparison_operator = models.CharField(max_length=4, default=">", choices=[(">", ">"), (">=", ">="), ("<", "<"), ("<=", "<=")])
    consecutive_samples = models.PositiveIntegerField(default=1)
    recovery_samples = models.PositiveIntegerField(default=1)
    cooldown_seconds = models.PositiveIntegerField(default=300)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True, related_name="alert_rules")
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True, blank=True, related_name="alert_rules")
    include_admin_down = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
