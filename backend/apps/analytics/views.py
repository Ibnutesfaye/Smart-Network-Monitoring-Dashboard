from datetime import timedelta
from typing import ClassVar

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import Alert
from apps.audit.models import ActivityLog
from apps.devices.models import Device
from apps.traffic.models import TrafficSample

from .risk import calculate_health_score, calculate_risk_score


class DeviceGrowthView(APIView):
    permission_classes: ClassVar = [IsAuthenticated]

    def get(self, request):
        since = timezone.now() - timedelta(days=30)
        data = (
            Device.objects.filter(created_at__gte=since)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        return Response(list(data))


class TrafficTrendsView(APIView):
    permission_classes: ClassVar = [IsAuthenticated]

    def get(self, request):
        since = timezone.now() - timedelta(days=7)
        samples = (
            TrafficSample.objects.filter(timestamp__gte=since, device__isnull=True)
            .annotate(date=TruncDate("timestamp"))
            .values("date")
            .annotate(
                avg_upload=Count("upload_speed"),
                avg_bandwidth=Count("bandwidth_usage"),
            )
        )
        detailed = list(
            TrafficSample.objects.filter(timestamp__gte=since, device__isnull=True)
            .order_by("timestamp")
            .values("timestamp", "upload_speed", "download_speed", "bandwidth_usage")[:200]
        )
        return Response({"by_date": list(samples), "samples": detailed})


class AlertTrendsView(APIView):
    permission_classes: ClassVar = [IsAuthenticated]

    def get(self, request):
        since = timezone.now() - timedelta(days=30)
        by_date = (
            Alert.objects.filter(created_at__gte=since)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        by_level = (
            Alert.objects.filter(created_at__gte=since)
            .values("alert_level")
            .annotate(count=Count("id"))
        )
        return Response({"by_date": list(by_date), "by_level": list(by_level)})


class SecurityStatsView(APIView):
    permission_classes: ClassVar = [IsAuthenticated]

    def get(self, request):
        since = timezone.now() - timedelta(days=7)
        return Response(
            {
                "failed_access_alerts": Alert.objects.filter(
                    alert_type=Alert.AlertType.FAILED_ACCESS, created_at__gte=since
                ).count(),
                "suspicious_activity": Alert.objects.filter(
                    alert_type=Alert.AlertType.SUSPICIOUS_ACTIVITY, created_at__gte=since
                ).count(),
                "unknown_devices": Device.objects.filter(is_known=False).count(),
                "audit_events": ActivityLog.objects.filter(created_at__gte=since).count(),
                "risk_score": calculate_risk_score(),
            }
        )


class DashboardMetricsView(APIView):
    permission_classes: ClassVar = [IsAuthenticated]

    def get(self, request):
        total = Device.objects.count()
        online = Device.objects.filter(status=Device.Status.ONLINE).count()
        offline = Device.objects.filter(status=Device.Status.OFFLINE).count()
        active_alerts = Alert.objects.filter(acknowledged=False).count()
        latest_traffic = TrafficSample.objects.filter(device__isnull=True).first()
        recent_activity = list(
            ActivityLog.objects.select_related("user")
            .order_by("-created_at")[:10]
            .values("action", "description", "created_at", "user__username")
        )
        return Response(
            {
                "total_devices": total,
                "online_devices": online,
                "offline_devices": offline,
                "active_alerts": active_alerts,
                "traffic_summary": {
                    "upload": latest_traffic.upload_speed if latest_traffic else 0,
                    "download": latest_traffic.download_speed if latest_traffic else 0,
                    "bandwidth": latest_traffic.bandwidth_usage if latest_traffic else 0,
                },
                "network_health_score": calculate_health_score(),
                "risk_score": calculate_risk_score(),
                "recent_activities": recent_activity,
            }
        )
