from rest_framework import serializers

from .models import Incident, IncidentComment, IncidentEvent, MaintenanceWindow


class IncidentEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True, allow_null=True)

    class Meta:
        model = IncidentEvent
        fields = ("id", "event_type", "actor", "actor_name", "metadata", "created_at")


class IncidentCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)

    class Meta:
        model = IncidentComment
        fields = ("id", "incident", "author", "author_name", "body", "created_at", "updated_at")
        read_only_fields = ("incident", "author")


class IncidentSerializer(serializers.ModelSerializer):
    time_to_acknowledge = serializers.FloatField(read_only=True)
    time_to_resolve = serializers.FloatField(read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.username", read_only=True, allow_null=True)
    site_name = serializers.CharField(source="site.name", read_only=True, allow_null=True)

    class Meta:
        model = Incident
        fields = ("id", "incident_number", "title", "description", "status", "severity", "priority", "site", "site_name", "primary_device", "devices", "interfaces", "alerts", "assigned_to", "assigned_to_name", "created_by", "acknowledged_at", "resolved_at", "closed_at", "resolution_summary", "root_cause", "time_to_acknowledge", "time_to_resolve", "created_at", "updated_at")
        read_only_fields = ("incident_number", "status", "created_by", "acknowledged_at", "resolved_at", "closed_at", "created_at", "updated_at")


class MaintenanceWindowSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = MaintenanceWindow
        fields = ("id", "title", "description", "status", "start_at", "end_at", "sites", "devices", "interfaces", "created_by", "created_by_name", "approved_by", "cancelled_at", "created_at", "updated_at")
        read_only_fields = ("status", "created_by", "approved_by", "cancelled_at", "created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_at", getattr(self.instance, "start_at", None))
        end = attrs.get("end_at", getattr(self.instance, "end_at", None))
        if start and end and end <= start:
            raise serializers.ValidationError({"end_at": "End time must be later than start time."})
        if not any(attrs.get(key) for key in ("sites", "devices", "interfaces")) and not self.instance:
            raise serializers.ValidationError("Select at least one maintenance target.")
        return attrs
