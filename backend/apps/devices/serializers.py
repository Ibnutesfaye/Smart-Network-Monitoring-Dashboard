import ipaddress

from rest_framework import serializers

from .models import (
    Device,
    DeviceInterface,
    DeviceStatusHistory,
    NetworkSegment,
    Organization,
    Site,
)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = "__all__"


class NetworkSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkSegment
        fields = "__all__"

    def validate_cidr(self, value):
        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError as exc:
            raise serializers.ValidationError("Enter a valid IPv4 or IPv6 CIDR.") from exc
        if network.prefixlen == 0:
            raise serializers.ValidationError("Default-route CIDRs cannot authorize monitoring.")
        return str(network)


class DeviceInterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceInterface
        fields = "__all__"
        read_only_fields = ("inbound_octets", "outbound_octets", "inbound_errors", "outbound_errors", "inbound_discards", "outbound_discards", "utilization_in_pct", "utilization_out_pct", "last_polled_at")


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = (
            "id",
            "device_name",
            "site",
            "network_segment",
            "hostname",
            "ip_address",
            "mac_address",
            "vendor",
            "model",
            "serial_number",
            "operating_system",
            "ipv6_address",
            "device_type",
            "criticality",
            "lifecycle_status",
            "monitoring_enabled",
            "snmp_enabled",
            "snmp_version",
            "snmp_port",
            "snmp_profile",
            "snmp_status",
            "snmp_last_error_code",
            "status",
            "last_seen",
            "last_latency_ms",
            "current_packet_loss",
            "uptime_seconds",
            "consecutive_failures",
            "consecutive_successes",
            "first_discovered_at",
            "last_checked_at",
            "notes",
            "is_known",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "last_seen", "last_latency_ms", "current_packet_loss", "uptime_seconds", "consecutive_failures", "consecutive_successes", "first_discovered_at", "last_checked_at", "status", "snmp_status", "snmp_last_error_code")


class DeviceStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceStatusHistory
        fields = ("id", "status", "latency_ms", "recorded_at")


class DeviceHistorySerializer(serializers.Serializer):
    history = DeviceStatusHistorySerializer(many=True)
    availability_percent = serializers.FloatField()
