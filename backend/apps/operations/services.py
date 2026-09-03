from django.db import transaction
from django.db.models import Count, Max, Q
from django.utils import timezone

from apps.alerts.models import Alert
from apps.devices.models import Device, Site
from apps.monitoring.broadcast import broadcast_operational_event

from .models import Incident, IncidentEvent, MaintenanceWindow

TRANSITIONS = {
    "open": {"acknowledged", "investigating", "resolved"},
    "acknowledged": {"investigating", "mitigated", "resolved"},
    "investigating": {"mitigated", "resolved"},
    "mitigated": {"investigating", "resolved"},
    "resolved": {"investigating", "closed"},
    "closed": {"investigating"},
}


def site_scope(queryset, user, field="site_id"):
    if user.is_superuser or getattr(user, "is_administrator", False):
        return queryset
    ids = list(user.sites.values_list("id", flat=True))
    # Backward compatibility: users created before P2 have no scope records.
    # Once assignments exist, the boundary is enforced.
    if not ids:
        return queryset
    return queryset.filter(**{f"{field}__in": ids})


@transaction.atomic
def create_incident(validated_data, actor, alerts=()):
    incident = Incident.objects.create(created_by=actor, **validated_data)
    incident.incident_number = f"INC-{timezone.now():%Y}-{incident.pk:06d}"
    incident.save(update_fields=["incident_number"])
    if alerts:
        incident.alerts.set(alerts)
    IncidentEvent.objects.create(incident=incident, actor=actor, event_type="created")
    transaction.on_commit(lambda: broadcast_operational_event("incident.created", incident))
    return incident


@transaction.atomic
def transition_incident(incident, new_status, actor, resolution_summary=""):
    if new_status not in TRANSITIONS.get(incident.status, set()):
        raise ValueError(f"Transition from {incident.status} to {new_status} is not allowed.")
    old = incident.status
    incident.status = new_status
    now = timezone.now()
    if new_status == Incident.Status.ACKNOWLEDGED and not incident.acknowledged_at:
        incident.acknowledged_at = now
    if new_status == Incident.Status.RESOLVED:
        incident.resolved_at = now
        incident.resolution_summary = resolution_summary
    elif new_status == Incident.Status.INVESTIGATING:
        incident.resolved_at = None
        incident.closed_at = None
    elif new_status == Incident.Status.CLOSED:
        incident.closed_at = now
    incident.save()
    IncidentEvent.objects.create(incident=incident, actor=actor, event_type="status_changed", metadata={"from": old, "to": new_status})
    transaction.on_commit(lambda: broadcast_operational_event(f"incident.{new_status}", incident))
    return incident


def noc_summary(user):
    devices = site_scope(Device.objects.all(), user)
    alerts = site_scope(Alert.objects.filter(state__in=[Alert.State.FIRING, Alert.State.ACKNOWLEDGED]), user, "device__site_id")
    incidents = site_scope(Incident.objects.exclude(status__in=[Incident.Status.RESOLVED, Incident.Status.CLOSED]), user)
    maintenance = site_scope(MaintenanceWindow.objects.filter(status=MaintenanceWindow.Status.ACTIVE), user, "sites__id").distinct()
    counts = {row["status"]: row["count"] for row in devices.values("status").annotate(count=Count("id"))}
    alert_counts = {row["alert_level"]: row["count"] for row in alerts.values("alert_level").annotate(count=Count("id"))}
    total = devices.count()
    down = counts.get(Device.Status.OFFLINE, 0)
    degraded = counts.get(Device.Status.DEGRADED, 0)
    critical = alert_counts.get(Alert.Level.CRITICAL, 0)
    high = alert_counts.get(Alert.Level.HIGH, 0)
    open_incidents = incidents.count()
    penalty = (down * 15) + (degraded * 6) + (critical * 8) + (high * 4) + (open_incidents * 3)
    health = max(0, min(100, round(100 - penalty / max(total, 1))))
    sites = site_scope(Site.objects.filter(active=True), user, "id").annotate(
        total_devices=Count("devices", distinct=True),
        up_devices=Count("devices", filter=Q(devices__status=Device.Status.ONLINE), distinct=True),
        degraded_devices=Count("devices", filter=Q(devices__status=Device.Status.DEGRADED), distinct=True),
        down_devices=Count("devices", filter=Q(devices__status=Device.Status.OFFLINE), distinct=True),
        critical_alerts=Count("devices__alerts", filter=Q(devices__alerts__alert_level=Alert.Level.CRITICAL, devices__alerts__state__in=[Alert.State.FIRING, Alert.State.ACKNOWLEDGED]), distinct=True),
        open_incidents=Count("incidents", filter=~Q(incidents__status__in=[Incident.Status.RESOLVED, Incident.Status.CLOSED]), distinct=True),
        last_update=Max("devices__last_checked_at"),
    )
    site_rows = list(sites.values("id", "name", "total_devices", "up_devices", "degraded_devices", "down_devices", "critical_alerts", "open_incidents", "last_update"))
    for row in site_rows:
        row["health"] = max(0, 100 - row["down_devices"] * 20 - row["degraded_devices"] * 8 - row["critical_alerts"] * 10)
    site_rows.sort(key=lambda x: x["health"])
    return {
        "health_score": health,
        "health_contributors": {"down_devices": down, "degraded_devices": degraded, "critical_alerts": critical, "high_alerts": high, "open_incidents": open_incidents},
        "devices": {"total": total, "up": counts.get(Device.Status.ONLINE, 0), "degraded": degraded, "down": down, "maintenance": counts.get(Device.Status.MAINTENANCE, 0), "unknown": counts.get(Device.Status.UNKNOWN, 0)},
        "alerts": alert_counts,
        "open_incidents": open_incidents,
        "active_maintenance": maintenance.count(),
        "sites": site_rows,
        "sites_healthy": sum(1 for s in site_rows if s["health"] >= 90),
        "sites_total": len(site_rows),
        "last_monitoring_update": devices.aggregate(value=Max("last_checked_at"))["value"],
    }


@transaction.atomic
def evaluate_maintenance_windows(now=None):
    now = now or timezone.now()
    started = list(MaintenanceWindow.objects.select_for_update().filter(status=MaintenanceWindow.Status.SCHEDULED, start_at__lte=now, end_at__gt=now))
    completed = list(MaintenanceWindow.objects.select_for_update().filter(status__in=[MaintenanceWindow.Status.SCHEDULED, MaintenanceWindow.Status.ACTIVE], end_at__lte=now))
    for window in started:
        window.status = MaintenanceWindow.Status.ACTIVE
        window.save(update_fields=["status", "updated_at"])
        transaction.on_commit(lambda w=window: broadcast_operational_event("maintenance.started", w))
    for window in completed:
        window.status = MaintenanceWindow.Status.COMPLETED
        window.save(update_fields=["status", "updated_at"])
        transaction.on_commit(lambda w=window: broadcast_operational_event("maintenance.completed", w))
    return len(started), len(completed)
