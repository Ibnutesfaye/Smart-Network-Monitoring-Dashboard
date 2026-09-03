from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def initialize_alert_lifecycle(apps, schema_editor):
    Alert = apps.get_model("alerts", "Alert")
    for alert in Alert.objects.all().iterator():
        alert.state = "acknowledged" if alert.acknowledged else "firing"
        alert.deduplication_key = f"legacy:{alert.pk}"
        alert.first_triggered_at = alert.created_at
        alert.last_triggered_at = alert.created_at
        alert.save(update_fields=["state", "deduplication_key", "first_triggered_at", "last_triggered_at"])


class Migration(migrations.Migration):
    dependencies = [("devices", "0002_p1_monitoring_core"), migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("alerts", "0001_initial")]
    operations = [
        migrations.AlterField(model_name="alert", name="alert_type", field=models.CharField(choices=[("unknown_device", "Unknown Device Detected"), ("device_offline", "Device Offline"), ("high_bandwidth", "High Bandwidth Usage"), ("suspicious_activity", "Suspicious Activity"), ("failed_access", "Repeated Failed Access Attempts"), ("device_recovered", "Device Recovered"), ("high_latency", "High Latency"), ("packet_loss", "Packet Loss"), ("high_cpu", "High CPU"), ("high_memory", "High Memory"), ("interface_down", "Interface Down"), ("high_interface_utilization", "High Interface Utilization"), ("interface_errors", "Interface Errors")], db_index=True, max_length=32)),
        migrations.AlterField(model_name="alertrule", name="alert_type", field=models.CharField(choices=[("unknown_device", "Unknown Device Detected"), ("device_offline", "Device Offline"), ("high_bandwidth", "High Bandwidth Usage"), ("suspicious_activity", "Suspicious Activity"), ("failed_access", "Repeated Failed Access Attempts"), ("device_recovered", "Device Recovered"), ("high_latency", "High Latency"), ("packet_loss", "Packet Loss"), ("high_cpu", "High CPU"), ("high_memory", "High Memory"), ("interface_down", "Interface Down"), ("high_interface_utilization", "High Interface Utilization"), ("interface_errors", "Interface Errors")], max_length=32)),
        migrations.AddField(model_name="alert", name="state", field=models.CharField(choices=[("pending", "Pending"), ("firing", "Firing"), ("acknowledged", "Acknowledged"), ("resolved", "Resolved")], db_index=True, default="firing", max_length=16)),
        migrations.AddField(model_name="alert", name="deduplication_key", field=models.CharField(blank=True, db_index=True, max_length=255)),
        migrations.AddField(model_name="alert", name="first_triggered_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="alert", name="last_triggered_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="alert", name="occurrence_count", field=models.PositiveIntegerField(default=1)),
        migrations.AddField(model_name="alert", name="recovery_count", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="alert", name="acknowledged_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="alert", name="acknowledgement_note", field=models.TextField(blank=True)),
        migrations.AddField(model_name="alert", name="resolved_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="alert", name="acknowledged_by", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="acknowledged_alerts", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="alertrule", name="threshold", field=models.FloatField(blank=True, null=True)),
        migrations.AddField(model_name="alertrule", name="comparison_operator", field=models.CharField(choices=[(">", ">"), (">=", ">="), ("<", "<"), ("<=", "<=")], default=">", max_length=4)),
        migrations.AddField(model_name="alertrule", name="consecutive_samples", field=models.PositiveIntegerField(default=1)),
        migrations.AddField(model_name="alertrule", name="recovery_samples", field=models.PositiveIntegerField(default=1)),
        migrations.AddField(model_name="alertrule", name="cooldown_seconds", field=models.PositiveIntegerField(default=300)),
        migrations.AddField(model_name="alertrule", name="site", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="alert_rules", to="devices.site")),
        migrations.AddField(model_name="alertrule", name="device", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="alert_rules", to="devices.device")),
        migrations.RunPython(initialize_alert_lifecycle, migrations.RunPython.noop),
    ]
