from typing import ClassVar

from rest_framework import viewsets

from apps.accounts.permissions import IsAdministrator

from .models import ActivityLog
from .serializers import ActivityLogSerializer


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.select_related("user").all()
    serializer_class = ActivityLogSerializer
    permission_classes: ClassVar = [IsAdministrator]
    filterset_fields: ClassVar = ["action", "user"]
    search_fields: ClassVar = ["description", "action"]
    ordering: ClassVar = ["-created_at"]
