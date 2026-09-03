from django.db import transaction
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.devices.models import Device
from apps.monitoring.broadcast import broadcast_operational_event
from apps.operations.permissions import IsAdministratorOrScopedReadOnly
from apps.operations.services import site_scope

from .models import TopologyLink
from .serializers import TopologyLinkSerializer


class TopologyLinkViewSet(viewsets.ModelViewSet):
    serializer_class = TopologyLinkSerializer
    permission_classes = [IsAdministratorOrScopedReadOnly]
    filterset_fields = ["site", "status", "link_type", "discovery_source"]

    def get_queryset(self):
        return site_scope(TopologyLink.objects.select_related("site", "source_device", "target_device", "source_interface", "target_interface"), self.request.user)

    def perform_create(self, serializer):
        link = serializer.save()
        transaction.on_commit(lambda: broadcast_operational_event("topology.changed", link))

    def perform_update(self, serializer):
        link = serializer.save()
        transaction.on_commit(lambda: broadcast_operational_event("topology.changed", link))

    def perform_destroy(self, instance):
        link_id = instance.pk
        site_id = instance.site_id
        instance.delete()
        transaction.on_commit(lambda: broadcast_operational_event("topology.changed", type("DeletedLink", (), {"pk": link_id, "site_id": site_id})()))


class TopologyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        devices = site_scope(Device.objects.select_related("site").prefetch_related("alerts"), request.user)
        site_id = request.query_params.get("site")
        if site_id:
            devices = devices.filter(site_id=site_id)
        nodes = [{"id": str(d.id), "label": d.device_name, "ip": d.ip_address, "status": d.status, "type": d.device_type, "site": d.site_id, "criticality": d.criticality, "active_alerts": sum(1 for a in d.alerts.all() if a.state in {"firing", "acknowledged"}), "latency_ms": d.last_latency_ms, "packet_loss_pct": d.current_packet_loss, "last_seen": d.last_seen} for d in devices[:1000]]
        links = site_scope(TopologyLink.objects.select_related("source_interface", "target_interface"), request.user)
        if site_id:
            links = links.filter(site_id=site_id)
        edges = [{"id": link.id, "source": str(link.source_device_id), "target": str(link.target_device_id), "source_interface": link.source_interface.name if link.source_interface else None, "target_interface": link.target_interface.name if link.target_interface else None, "link_type": link.link_type, "status": link.status, "bandwidth_bps": link.bandwidth_bps, "last_seen": link.last_seen_at} for link in links[:1000]]
        return Response({"nodes": nodes, "edges": edges})
