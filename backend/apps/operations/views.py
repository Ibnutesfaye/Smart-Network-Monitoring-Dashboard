from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import Alert
from apps.devices.models import (
    Device,
    DeviceInterface,
    DeviceStatusHistory,
    InterfaceTelemetry,
)
from apps.monitoring.broadcast import broadcast_operational_event

from .models import Incident, IncidentEvent, MaintenanceWindow
from .permissions import IsOperator
from .serializers import (
    IncidentCommentSerializer,
    IncidentEventSerializer,
    IncidentSerializer,
    MaintenanceWindowSerializer,
)
from .services import create_incident, noc_summary, site_scope, transition_incident


class NocSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(noc_summary(request.user))


RANGES = {"1h": 1 / 24, "6h": 0.25, "24h": 1, "7d": 7, "30d": 30}


class NocAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        range_name = request.query_params.get("range", "24h")
        if range_name not in RANGES:
            return Response({"detail": "Unsupported range."}, status=400)
        devices = site_scope(Device.objects.all(), request.user)
        if request.query_params.get("site"):
            devices = devices.filter(site_id=request.query_params["site"])
        since = timezone.now() - timedelta(days=RANGES[range_name])
        rows = DeviceStatusHistory.objects.filter(device__in=devices, recorded_at__gte=since).values("recorded_at", "status").order_by("recorded_at")[:5000]
        buckets = {}
        for row in rows:
            stamp = row["recorded_at"].replace(minute=0, second=0, microsecond=0)
            bucket = buckets.setdefault(stamp, {"up": 0, "total": 0})
            bucket["total"] += 1
            bucket["up"] += row["status"] == Device.Status.ONLINE
        results = [{"timestamp": stamp, "availability_pct": round(value["up"] / value["total"] * 100, 2)} for stamp, value in buckets.items()]
        return Response({"range": range_name, "results": results[-720:]})


class NocTrafficView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        interfaces = site_scope(DeviceInterface.objects.select_related("device"), request.user, "device__site_id")
        if request.query_params.get("site"):
            interfaces = interfaces.filter(device__site_id=request.query_params["site"])
        known = interfaces.exclude(utilization_in_pct__isnull=True, utilization_out_pct__isnull=True)
        top = sorted(known[:2000], key=lambda item: max(item.utilization_in_pct or 0, item.utilization_out_pct or 0), reverse=True)[:10]
        latest = InterfaceTelemetry.objects.filter(interface__in=interfaces).aggregate(inbound_bps=Max("inbound_bps"), outbound_bps=Max("outbound_bps"))
        return Response({"inbound_bps": latest["inbound_bps"], "outbound_bps": latest["outbound_bps"], "top_interfaces": [{"id": item.id, "device_id": item.device_id, "device": item.device.device_name, "name": item.name, "in_pct": item.utilization_in_pct, "out_pct": item.utilization_out_pct} for item in top]})


class NocProblemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        devices = site_scope(Device.objects.all(), request.user).annotate(active_alerts=Count("alerts", filter=Q(alerts__state__in=[Alert.State.FIRING, Alert.State.ACKNOWLEDGED])))
        alert_heavy = devices.filter(active_alerts__gt=0).order_by("-active_alerts")[:10]
        long_down = devices.filter(status=Device.Status.OFFLINE).order_by("last_seen")[:10]
        high_latency = devices.exclude(last_latency_ms__isnull=True).order_by("-last_latency_ms")[:10]
        return Response({"most_alerts": [{"id": d.id, "name": d.device_name, "value": d.active_alerts} for d in alert_heavy], "longest_down": [{"id": d.id, "name": d.device_name, "last_seen": d.last_seen} for d in long_down], "highest_latency": [{"id": d.id, "name": d.device_name, "value": d.last_latency_ms} for d in high_latency]})


class IncidentViewSet(viewsets.ModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [IsOperator]
    filterset_fields = ["status", "priority", "severity", "site", "assigned_to", "primary_device", "devices", "interfaces", "alerts"]
    search_fields = ["incident_number", "title", "description"]
    ordering_fields = ["created_at", "updated_at", "priority", "severity"]

    def get_queryset(self):
        return site_scope(Incident.objects.select_related("site", "assigned_to", "created_by").prefetch_related("alerts", "devices", "interfaces"), self.request.user)

    def perform_create(self, serializer):
        data = dict(serializer.validated_data)
        alerts = data.pop("alerts", [])
        devices = data.pop("devices", [])
        interfaces = data.pop("interfaces", [])
        incident = create_incident(data, self.request.user, alerts)
        incident.devices.set(devices)
        incident.interfaces.set(interfaces)
        serializer.instance = incident

    def perform_update(self, serializer):
        if "assigned_to" in serializer.validated_data and self.request.user.role != "administrator":
            serializer.validated_data.pop("assigned_to")
        serializer.save()

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        try:
            incident = transition_incident(self.get_object(), request.data.get("status", ""), request.user, str(request.data.get("resolution_summary", ""))[:10000])
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(incident).data)

    @action(detail=True, methods=["post"])
    def assign_to_me(self, request, pk=None):
        incident = self.get_object()
        incident.assigned_to = request.user
        incident.save(update_fields=["assigned_to", "updated_at"])
        IncidentEvent.objects.create(incident=incident, actor=request.user, event_type="assigned", metadata={"user_id": request.user.pk})
        transaction.on_commit(lambda: broadcast_operational_event("incident.assigned", incident))
        return Response(self.get_serializer(incident).data)

    @action(detail=True, methods=["post"])
    def attach_alert(self, request, pk=None):
        incident = self.get_object()
        alert = Alert.objects.select_related("device").get(pk=request.data.get("alert_id"))
        if incident.site_id and alert.device_id and alert.device.site_id != incident.site_id:
            return Response({"detail": "Alert is outside the incident site."}, status=400)
        incident.alerts.add(alert)
        IncidentEvent.objects.create(incident=incident, actor=request.user, event_type="alert_attached", metadata={"alert_id": alert.pk})
        return Response(self.get_serializer(incident).data)

    @action(detail=True, methods=["post"])
    def detach_alert(self, request, pk=None):
        incident = self.get_object()
        alert_id = request.data.get("alert_id")
        incident.alerts.remove(alert_id)
        IncidentEvent.objects.create(incident=incident, actor=request.user, event_type="alert_detached", metadata={"alert_id": alert_id})
        return Response(self.get_serializer(incident).data)

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, pk=None):
        incident = self.get_object()
        if request.method == "GET":
            return Response(IncidentCommentSerializer(incident.comments.select_related("author"), many=True).data)
        serializer = IncidentCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(incident=incident, author=request.user)
        IncidentEvent.objects.create(incident=incident, actor=request.user, event_type="comment_added", metadata={"comment_id": comment.pk})
        return Response(IncidentCommentSerializer(comment).data, status=201)

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        return Response(IncidentEventSerializer(self.get_object().events.select_related("actor"), many=True).data)


class MaintenanceWindowViewSet(viewsets.ModelViewSet):
    serializer_class = MaintenanceWindowSerializer
    permission_classes = [IsOperator]
    filterset_fields = ["status", "sites", "devices", "interfaces"]
    search_fields = ["title", "description"]
    ordering_fields = ["start_at", "end_at", "created_at"]

    def get_queryset(self):
        return site_scope(MaintenanceWindow.objects.select_related("created_by", "approved_by").prefetch_related("sites", "devices", "interfaces"), self.request.user, "sites__id").distinct()

    def perform_create(self, serializer):
        window = serializer.save(created_by=self.request.user)
        transaction.on_commit(lambda: broadcast_operational_event("maintenance.scheduled", window))

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        window = self.get_object()
        if window.status in {MaintenanceWindow.Status.COMPLETED, MaintenanceWindow.Status.CANCELLED}:
            return Response({"detail": "This maintenance window cannot be cancelled."}, status=400)
        window.status = MaintenanceWindow.Status.CANCELLED
        window.cancelled_at = timezone.now()
        window.save(update_fields=["status", "cancelled_at", "updated_at"])
        transaction.on_commit(lambda: broadcast_operational_event("maintenance.cancelled", window))
        return Response(self.get_serializer(window).data)
