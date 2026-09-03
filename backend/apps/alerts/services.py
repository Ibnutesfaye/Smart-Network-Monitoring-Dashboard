from django.conf import settings
from django.core.mail import send_mail
from django.db import models, transaction

from apps.monitoring.broadcast import broadcast_alert

from .models import Alert


def create_alert(device, alert_type, alert_level, message):
    alert = Alert.objects.create(
        device=device,
        alert_type=alert_type,
        alert_level=alert_level,
        message=message,
    )
    apply_maintenance_context(alert)
    transaction.on_commit(lambda: broadcast_alert(alert))
    if alert_level == Alert.Level.CRITICAL and not alert.maintenance_suppressed:
        send_critical_email(alert)
    return alert


def apply_maintenance_context(alert):
    from django.utils import timezone

    from apps.operations.models import MaintenanceWindow

    if not alert.device_id:
        return alert
    now = timezone.now()
    targets = models.Q(devices=alert.device) | models.Q(sites=alert.device.site)
    if alert.interface_id:
        targets |= models.Q(interfaces=alert.interface)
    window = MaintenanceWindow.objects.filter(status=MaintenanceWindow.Status.ACTIVE, start_at__lte=now, end_at__gt=now).filter(targets).distinct().first()
    if window:
        alert.maintenance_suppressed = True
        alert.maintenance_window = window
        alert.save(update_fields=["maintenance_suppressed", "maintenance_window"])
    return alert


def send_critical_email(alert):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    admins = User.objects.filter(role="administrator", email__isnull=False).exclude(email="")
    emails = [u.email for u in admins if u.email]
    if not emails:
        return
    send_mail(
        subject=f"[CRITICAL] SNMADMDCP Alert: {alert.alert_type}",
        message=alert.message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=emails,
        fail_silently=True,
    )
