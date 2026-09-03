from django.db import transaction
from django.db.models import F
from django.db import models
from django.utils import timezone

from .models import Alert, AlertRule
from apps.monitoring.broadcast import broadcast_alert


def _dedup(alert_type, device_id, rule_id=None, interface_id=None):
    resource = f"interface:{interface_id}" if interface_id else f"device:{device_id}"
    return f"{alert_type}:{resource}:rule:{rule_id or 'system'}"


def fire_or_update(device, alert_type, severity, message, rule=None, pending=False, interface=None):
    key = _dedup(alert_type, device.id, rule.id if rule else None, interface.id if interface else None)
    alert = Alert.objects.filter(deduplication_key=key).exclude(state=Alert.State.RESOLVED).first()
    now = timezone.now()
    required = rule.consecutive_samples if rule else 1
    if alert:
        next_count = alert.occurrence_count + 1
        alert.occurrence_count = F("occurrence_count") + 1
        alert.last_triggered_at = now
        alert.message = message
        alert.recovery_count = 0
        if alert.state == Alert.State.PENDING and next_count >= required:
            alert.state = Alert.State.FIRING
        alert.save(update_fields=["occurrence_count", "last_triggered_at", "message", "state", "recovery_count"])
        alert.refresh_from_db()
        if alert.state == Alert.State.FIRING:
            transaction.on_commit(lambda: broadcast_alert(alert, "alert.fired"))
        return alert
    alert = Alert.objects.create(device=device, interface=interface, alert_type=alert_type, alert_level=severity, message=message, state=Alert.State.PENDING if pending or required > 1 else Alert.State.FIRING, deduplication_key=key, first_triggered_at=now, last_triggered_at=now)
    from .services import apply_maintenance_context
    apply_maintenance_context(alert)
    if alert.state == Alert.State.FIRING:
        transaction.on_commit(lambda: broadcast_alert(alert, "alert.fired"))
    return alert


def resolve(device, alert_type, rule=None, interface=None):
    key = _dedup(alert_type, device.id, rule.id if rule else None, interface.id if interface else None)
    now = timezone.now()
    alerts = list(Alert.objects.filter(deduplication_key=key).exclude(state=Alert.State.RESOLVED))
    for alert in alerts:
        alert.recovery_count += 1
        required = rule.recovery_samples if rule else 1
        if alert.recovery_count < required:
            alert.save(update_fields=["recovery_count"])
            continue
        alert.state = Alert.State.RESOLVED
        alert.resolved_at = now
        alert.save(update_fields=["state", "resolved_at", "recovery_count"])
        transaction.on_commit(lambda current=alert: broadcast_alert(current, "alert.resolved"))
    return sum(1 for alert in alerts if alert.state == Alert.State.RESOLVED)


def evaluate_device_alerts(device, result, previous_status):
    if device.status == device.Status.OFFLINE:
        fire_or_update(device, Alert.AlertType.DEVICE_OFFLINE, Alert.Level.HIGH, f"Device {device.device_name} is down")
    elif device.status == device.Status.ONLINE:
        if resolve(device, Alert.AlertType.DEVICE_OFFLINE):
            fire_or_update(device, Alert.AlertType.DEVICE_RECOVERED, Alert.Level.LOW, f"Device {device.device_name} recovered")
    metric_map = {
        Alert.AlertType.HIGH_LATENCY: result.latency_ms,
        Alert.AlertType.PACKET_LOSS: result.packet_loss_pct,
        Alert.AlertType.HIGH_CPU: result.cpu_pct,
        Alert.AlertType.HIGH_MEMORY: result.memory_pct,
    }
    rules = AlertRule.objects.filter(is_active=True, alert_type__in=metric_map)
    rules = rules.filter(device__isnull=True) | rules.filter(device=device)
    for rule in rules:
        if rule.site_id and rule.site_id != device.site_id:
            continue
        value = metric_map.get(rule.alert_type)
        threshold = rule.threshold
        matched = value is not None and threshold is not None and {">": value > threshold, ">=": value >= threshold, "<": value < threshold, "<=": value <= threshold}[rule.comparison_operator]
        if matched:
            fire_or_update(device, rule.alert_type, rule.alert_level, f"{rule.name}: {value} {rule.comparison_operator} {threshold}", rule)
        else:
            resolve(device, rule.alert_type, rule)


def evaluate_interface_alerts(interface, telemetry):
    types = [Alert.AlertType.INTERFACE_DOWN, Alert.AlertType.HIGH_INTERFACE_UTILIZATION, Alert.AlertType.INTERFACE_ERRORS]
    rules = AlertRule.objects.filter(is_active=True, alert_type__in=types).filter(models.Q(device__isnull=True) | models.Q(device=interface.device))
    for rule in rules:
        if rule.site_id and rule.site_id != interface.device.site_id:
            continue
        if rule.alert_type == Alert.AlertType.INTERFACE_DOWN:
            matched = interface.oper_status == "down" and (interface.admin_status == "up" or rule.include_admin_down)
            value = interface.oper_status
        elif rule.alert_type == Alert.AlertType.HIGH_INTERFACE_UTILIZATION:
            values = [value for value in (telemetry.utilization_in_pct, telemetry.utilization_out_pct) if value is not None]
            value = max(values) if values else None
            matched = value is not None and rule.threshold is not None and value > rule.threshold
        else:
            deltas = [telemetry.inbound_errors_delta, telemetry.outbound_errors_delta, telemetry.inbound_discards_delta, telemetry.outbound_discards_delta]
            value = sum(item for item in deltas if item is not None) if any(item is not None for item in deltas) else None
            matched = value is not None and rule.threshold is not None and value > rule.threshold
        if matched:
            fire_or_update(interface.device, rule.alert_type, rule.alert_level, f"{rule.name} on {interface.name}: {value}", rule, interface=interface)
        else:
            resolve(interface.device, rule.alert_type, rule, interface=interface)
