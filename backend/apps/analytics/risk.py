from datetime import timedelta

from django.utils import timezone

from apps.alerts.models import Alert
from apps.devices.models import Device


def calculate_risk_score():
    """Return risk score 0-100 (higher = more risk)."""
    since = timezone.now() - timedelta(hours=24)
    score = 0
    critical = Alert.objects.filter(
        alert_level=Alert.Level.CRITICAL, created_at__gte=since, acknowledged=False
    ).count()
    score += min(critical * 15, 45)
    unknown = Device.objects.filter(is_known=False).count()
    score += min(unknown * 10, 30)
    high_bw = Alert.objects.filter(
        alert_type=Alert.AlertType.HIGH_BANDWIDTH, created_at__gte=since
    ).count()
    score += min(high_bw * 5, 25)
    offline = Device.objects.filter(status=Device.Status.OFFLINE).count()
    total = Device.objects.count() or 1
    score += min(int((offline / total) * 100 * 0.2), 20)
    return min(score, 100)


def calculate_health_score():
    """Return health score 0-100 (higher = healthier)."""
    total = Device.objects.count()
    if total == 0:
        return 100
    online = Device.objects.filter(status=Device.Status.ONLINE).count()
    online_pct = (online / total) * 100
    critical = Alert.objects.filter(
        alert_level=Alert.Level.CRITICAL, acknowledged=False
    ).count()
    critical_penalty = min(critical * 10, 40)
    risk = calculate_risk_score()
    health = (online_pct * 0.6) + ((100 - risk) * 0.4) - critical_penalty
    return max(0, min(100, round(health, 1)))
