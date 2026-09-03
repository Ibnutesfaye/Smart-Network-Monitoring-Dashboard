from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Incident(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        INVESTIGATING = "investigating", "Investigating"
        MITIGATED = "mitigated", "Mitigated"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Priority(models.TextChoices):
        P1 = "p1", "P1"
        P2 = "p2", "P2"
        P3 = "p3", "P3"
        P4 = "p4", "P4"

    incident_number = models.CharField(max_length=24, unique=True, null=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.MEDIUM, db_index=True)
    priority = models.CharField(max_length=4, choices=Priority.choices, default=Priority.P3, db_index=True)
    site = models.ForeignKey("devices.Site", null=True, blank=True, on_delete=models.PROTECT, related_name="incidents")
    primary_device = models.ForeignKey("devices.Device", null=True, blank=True, on_delete=models.SET_NULL, related_name="primary_incidents")
    devices = models.ManyToManyField("devices.Device", blank=True, related_name="incidents")
    interfaces = models.ManyToManyField("devices.DeviceInterface", blank=True, related_name="incidents")
    alerts = models.ManyToManyField("alerts.Alert", blank=True, related_name="incidents")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_incidents")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_incidents")
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    resolution_summary = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["site", "status", "created_at"]), models.Index(fields=["assigned_to", "status"])]

    @property
    def time_to_acknowledge(self):
        return (self.acknowledged_at - self.created_at).total_seconds() if self.acknowledged_at else None

    @property
    def time_to_resolve(self):
        return (self.resolved_at - self.created_at).total_seconds() if self.resolved_at else None


class IncidentEvent(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=32)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]


class IncidentComment(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = models.TextField(max_length=10000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class MaintenanceWindow(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField(db_index=True)
    sites = models.ManyToManyField("devices.Site", blank=True, related_name="maintenance_windows")
    devices = models.ManyToManyField("devices.Device", blank=True, related_name="maintenance_windows")
    interfaces = models.ManyToManyField("devices.DeviceInterface", blank=True, related_name="maintenance_windows")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_maintenance")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_maintenance")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_at"]
        indexes = [models.Index(fields=["status", "start_at", "end_at"])]

    def clean(self):
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError({"end_at": "End time must be later than start time."})

    def affects(self, device=None, interface=None):
        now = timezone.now()
        if self.status != self.Status.ACTIVE or not self.start_at <= now < self.end_at:
            return False
        if interface and self.interfaces.filter(pk=interface.pk).exists():
            return True
        if device and (self.devices.filter(pk=device.pk).exists() or (device.site_id and self.sites.filter(pk=device.site_id).exists())):
            return True
        return False
