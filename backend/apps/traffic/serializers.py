from rest_framework import serializers


from .models import TrafficSample


class TrafficSampleSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source="device.device_name", read_only=True, allow_null=True)

    class Meta:
        model = TrafficSample
        fields = (
            "id",
            "device",
            "device_name",
            "upload_speed",
            "download_speed",
            "bandwidth_usage",
            "timestamp",
        )


class TrafficSummarySerializer(serializers.Serializer):
    current_upload = serializers.FloatField()
    current_download = serializers.FloatField()
    total_bandwidth = serializers.FloatField()
    peak_upload = serializers.FloatField()
    peak_download = serializers.FloatField()
    avg_bandwidth = serializers.FloatField()
    sample_count = serializers.IntegerField()
