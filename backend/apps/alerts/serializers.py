from rest_framework import serializers

from .models import Alert, AlertRule


class AlertSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source="device.device_name", read_only=True, allow_null=True)
    interface_name = serializers.CharField(source="interface.name", read_only=True, allow_null=True)

    class Meta:
        model = Alert
        fields = (
            "id",
            "device",
            "device_name",
            "interface",
            "interface_name",
            "alert_level",
            "alert_type",
            "message",
            "acknowledged",
            "state",
            "deduplication_key",
            "first_triggered_at",
            "last_triggered_at",
            "occurrence_count",
            "recovery_count",
            "acknowledged_at",
            "acknowledged_by",
            "acknowledgement_note",
            "resolved_at",
            "maintenance_suppressed",
            "maintenance_window",
            "created_at",
        )
        read_only_fields = ("deduplication_key", "first_triggered_at", "last_triggered_at", "occurrence_count", "recovery_count", "acknowledged_at", "acknowledged_by", "resolved_at", "maintenance_suppressed", "maintenance_window")


class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = "__all__"
