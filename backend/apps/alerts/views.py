from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone

from apps.accounts.permissions import IsAdministrator, IsAdministratorOrReadOnly
from apps.audit.utils import log_activity
from apps.monitoring.broadcast import broadcast_alert
from apps.operations.services import site_scope

from .models import Alert, AlertRule
from .serializers import AlertRuleSerializer, AlertSerializer


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.select_related("device", "interface").all()
    serializer_class = AlertSerializer
    permission_classes = [IsAdministratorOrReadOnly]
    filterset_fields = ["alert_level", "alert_type", "state", "acknowledged", "device", "interface"]
    search_fields = ["message"]
    ordering_fields = ["created_at", "alert_level", "first_triggered_at", "last_triggered_at", "occurrence_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return site_scope(super().get_queryset(), self.request.user, "device__site_id")

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.acknowledged = True
        alert.state = Alert.State.ACKNOWLEDGED
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.acknowledgement_note = str(request.data.get("note", ""))[:2000]
        alert.save(update_fields=["acknowledged", "state", "acknowledged_by", "acknowledged_at", "acknowledgement_note"])
        log_activity(request.user, "alert_acknowledged", f"Acknowledged alert {alert.pk}", request)
        transaction.on_commit(lambda: broadcast_alert(alert, event="alert.acknowledged"))
        return Response(AlertSerializer(alert).data)


class AlertRuleViewSet(viewsets.ModelViewSet):
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    permission_classes = [IsAdministrator]
