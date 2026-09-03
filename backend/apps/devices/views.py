from typing import ClassVar

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdministrator, IsAdministratorOrReadOnly
from apps.audit.utils import log_activity
from apps.monitoring.tasks import discover_devices
from apps.operations.services import site_scope

from .models import Device, DeviceInterface, NetworkSegment, Organization, Site
from .serializers import (
    DeviceInterfaceSerializer,
    DeviceSerializer,
    NetworkSegmentSerializer,
    OrganizationSerializer,
    SiteSerializer,
)


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes: ClassVar = [IsAdministratorOrReadOnly]
    filterset_fields: ClassVar = ["active"]
    search_fields: ClassVar = ["name", "code"]


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.select_related("organization")
    serializer_class = SiteSerializer
    permission_classes: ClassVar = [IsAdministratorOrReadOnly]
    filterset_fields: ClassVar = ["organization", "active"]
    search_fields: ClassVar = ["name", "code"]

    def get_queryset(self):
        return site_scope(super().get_queryset(), self.request.user, "id")


class NetworkSegmentViewSet(viewsets.ModelViewSet):
    queryset = NetworkSegment.objects.select_related("site", "site__organization")
    serializer_class = NetworkSegmentSerializer
    permission_classes: ClassVar = [IsAdministratorOrReadOnly]
    filterset_fields: ClassVar = ["site", "active", "monitoring_enabled", "discovery_enabled"]

    def get_queryset(self):
        return site_scope(super().get_queryset(), self.request.user)


class DeviceInterfaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DeviceInterface.objects.select_related("device", "device__site")
    serializer_class = DeviceInterfaceSerializer
    filterset_fields: ClassVar = ["device", "oper_status", "admin_status"]
    search_fields: ClassVar = ["name", "alias", "description", "mac_address"]

    def get_queryset(self):
        return site_scope(super().get_queryset(), self.request.user, "device__site_id")


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.select_related("site", "network_segment")
    serializer_class = DeviceSerializer
    permission_classes: ClassVar = [IsAdministratorOrReadOnly]
    filterset_fields: ClassVar = ["site", "network_segment", "status", "device_type", "criticality", "vendor", "is_known", "monitoring_enabled"]
    search_fields: ClassVar = ["device_name", "hostname", "ip_address", "mac_address", "vendor"]
    ordering_fields: ClassVar = ["device_name", "ip_address", "last_seen", "status", "created_at"]
    ordering: ClassVar = ["-last_seen"]

    def get_queryset(self):
        return site_scope(super().get_queryset(), self.request.user)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        device = self.get_object()
        history = device.status_history.all()[:500]
        total = history.count()
        online_count = history.filter(status=Device.Status.ONLINE).count()
        availability = (online_count / total * 100) if total else 0.0
        from .serializers import DeviceStatusHistorySerializer

        return Response(
            {
                "history": DeviceStatusHistorySerializer(history, many=True).data,
                "availability_percent": round(availability, 2),
            }
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAdministrator])
    def discover(self, request):
        discover_devices.delay()
        log_activity(request.user, "device_discover", "Manual device discovery triggered", request)
        return Response({"detail": "Discovery started."}, status=status.HTTP_202_ACCEPTED)
