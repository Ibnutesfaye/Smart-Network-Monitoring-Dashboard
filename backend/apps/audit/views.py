from rest_framework import viewsets

from apps.accounts.permissions import IsAdministrator

from .models import ActivityLog
from .serializers import ActivityLogSerializer


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.select_related("user").all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAdministrator]
    filterset_fields = ["action", "user"]
    search_fields = ["description", "action"]
    ordering = ["-created_at"]
