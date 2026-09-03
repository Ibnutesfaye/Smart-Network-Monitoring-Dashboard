from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.devices.models import (
    Device,
    DeviceInterface,
    DeviceTelemetry,
    InterfaceTelemetry,
)

RANGES = {"1h": timedelta(hours=1), "6h": timedelta(hours=6), "24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}
MAX_POINTS = 1000


def _bounded_samples(queryset):
    count = queryset.count()
    step = max(1, (count + MAX_POINTS - 1) // MAX_POINTS)
    values = list(queryset.values()[::step])
    return values[-MAX_POINTS:]


class TelemetryRangeView(APIView):
    model = None
    parent_model = None
    parent_field = None

    def get(self, request, pk):
        parent = get_object_or_404(self.parent_model, pk=pk)
        range_name = request.query_params.get("range", "24h")
        if range_name not in RANGES:
            return Response({"detail": f"range must be one of: {', '.join(RANGES)}"}, status=400)
        since = timezone.now() - RANGES[range_name]
        queryset = self.model.objects.filter(**{self.parent_field: parent}, timestamp__gte=since).order_by("timestamp")
        return Response({"range": range_name, "count": queryset.count(), "results": _bounded_samples(queryset)})


class DeviceTelemetryView(TelemetryRangeView):
    model = DeviceTelemetry
    parent_model = Device
    parent_field = "device"


class InterfaceTelemetryView(TelemetryRangeView):
    model = InterfaceTelemetry
    parent_model = DeviceInterface
    parent_field = "interface"
