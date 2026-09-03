from datetime import timedelta

from django.db.models import Avg, Max
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import TrafficSample
from .serializers import TrafficSampleSerializer, TrafficSummarySerializer


class TrafficViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TrafficSample.objects.select_related("device").all()
    serializer_class = TrafficSampleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["device"]
    ordering_fields = ["timestamp", "bandwidth_usage"]
    ordering = ["-timestamp"]

    def get_queryset(self):
        qs = super().get_queryset()
        device_id = self.request.query_params.get("device_id")
        if device_id:
            qs = qs.filter(device_id=device_id)
        date_from = self.request.query_params.get("from")
        date_to = self.request.query_params.get("to")
        if date_from:
            qs = qs.filter(timestamp__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__lte=date_to)
        return qs

    @action(detail=False, methods=["get"])
    def summary(self, request):
        since = timezone.now() - timedelta(hours=24)
        samples = TrafficSample.objects.filter(timestamp__gte=since, device__isnull=True)
        if not samples.exists():
            samples = TrafficSample.objects.filter(timestamp__gte=since)
        latest = samples.first()
        agg = samples.aggregate(
            peak_upload=Max("upload_speed"),
            peak_download=Max("download_speed"),
            avg_bandwidth=Avg("bandwidth_usage"),
        )
        data = {
            "current_upload": latest.upload_speed if latest else 0,
            "current_download": latest.download_speed if latest else 0,
            "total_bandwidth": latest.bandwidth_usage if latest else 0,
            "peak_upload": agg["peak_upload"] or 0,
            "peak_download": agg["peak_download"] or 0,
            "avg_bandwidth": agg["avg_bandwidth"] or 0,
            "sample_count": samples.count(),
        }
        return Response(TrafficSummarySerializer(data).data)
