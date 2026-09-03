from dataclasses import dataclass

from django.conf import settings
from django.db import transaction

from apps.alerts.engine import evaluate_device_alerts, evaluate_interface_alerts
from apps.devices.models import (
    Device,
    DeviceInterface,
    DeviceStatusHistory,
    DeviceTelemetry,
    InterfaceTelemetry,
)
from apps.monitoring.authorization import require_authorized_device

from .broadcast import broadcast_device


@dataclass(frozen=True)
class CounterRates:
    inbound_bps: float | None = None
    outbound_bps: float | None = None
    utilization_in_pct: float | None = None
    utilization_out_pct: float | None = None


def calculate_counter_rates(previous, current, elapsed_seconds, speed_bps=None):
    if previous is None or current is None or elapsed_seconds <= 0 or current < previous:
        return None
    rate = (current - previous) * 8 / elapsed_seconds
    if rate < 0 or (speed_bps and rate > speed_bps * 1.2):
        return None
    return rate


def utilization(rate, speed_bps):
    if rate is None or not speed_bps:
        return None
    return round(min(100.0, max(0.0, rate / speed_bps * 100)), 3)


def counter_delta(previous, current):
    if previous is None or current is None or current < previous:
        return None
    return current - previous


def _next_status(device, reachable):
    if reachable:
        successes = device.consecutive_successes + 1
        failures = 0
        status = device.status
        if successes >= settings.MONITOR_RECOVERY_THRESHOLD:
            status = Device.Status.ONLINE
        elif status == Device.Status.OFFLINE:
            status = Device.Status.DEGRADED
    else:
        failures = device.consecutive_failures + 1
        successes = 0
        status = Device.Status.OFFLINE if failures >= settings.MONITOR_FAILURE_THRESHOLD else Device.Status.DEGRADED
    return status, failures, successes


def process_monitoring_result(device_id, result):
    require_authorized_device(Device.objects.select_related("site").get(pk=device_id))
    with transaction.atomic():
        device = Device.objects.select_for_update().get(pk=device_id)
        if device.last_checked_at and result.collected_at <= device.last_checked_at:
            return device
        previous_status = device.status
        device.status, device.consecutive_failures, device.consecutive_successes = _next_status(device, result.reachable)
        device.last_checked_at = result.collected_at
        device.last_latency_ms = result.latency_ms
        device.current_packet_loss = result.packet_loss_pct
        device.uptime_seconds = result.uptime_seconds
        if "snmp" in result.source:
            device.snmp_status = "available" if result.interfaces or result.metadata else "unavailable"
            device.snmp_last_error_code = result.errors[0] if result.errors else ""
        if result.reachable:
            device.last_seen = result.collected_at
        device.save()
        DeviceTelemetry.objects.create(device=device, timestamp=result.collected_at, latency_ms=result.latency_ms, packet_loss_pct=result.packet_loss_pct, cpu_pct=result.cpu_pct, memory_pct=result.memory_pct, uptime_seconds=result.uptime_seconds, reachable=result.reachable, source=result.source)
        DeviceStatusHistory.objects.create(device=device, status=device.status, latency_ms=result.latency_ms)
        interface_events = []
        for sample in result.interfaces:
            interface, _ = DeviceInterface.objects.select_for_update().get_or_create(device=device, if_index=sample.if_index, defaults={"name": sample.name})
            elapsed = (result.collected_at - interface.last_polled_at).total_seconds() if interface.last_polled_at else 0
            inbound_bps = calculate_counter_rates(interface.inbound_octets, sample.inbound_octets, elapsed, sample.speed_bps)
            outbound_bps = calculate_counter_rates(interface.outbound_octets, sample.outbound_octets, elapsed, sample.speed_bps)
            error_deltas = {
                "inbound_errors_delta": counter_delta(interface.inbound_errors, sample.inbound_errors),
                "outbound_errors_delta": counter_delta(interface.outbound_errors, sample.outbound_errors),
                "inbound_discards_delta": counter_delta(interface.inbound_discards, sample.inbound_discards),
                "outbound_discards_delta": counter_delta(interface.outbound_discards, sample.outbound_discards),
            }
            previous_oper_status = interface.oper_status
            for field in ("name", "description", "mac_address", "admin_status", "oper_status", "speed_bps", "mtu", "interface_type", "alias", "inbound_octets", "outbound_octets", "inbound_errors", "outbound_errors", "inbound_discards", "outbound_discards"):
                setattr(interface, field, getattr(sample, field))
            interface.utilization_in_pct = utilization(inbound_bps, sample.speed_bps)
            interface.utilization_out_pct = utilization(outbound_bps, sample.speed_bps)
            interface.last_polled_at = result.collected_at
            interface.save()
            telemetry = InterfaceTelemetry.objects.create(interface=interface, timestamp=result.collected_at, inbound_bps=inbound_bps, outbound_bps=outbound_bps, utilization_in_pct=interface.utilization_in_pct, utilization_out_pct=interface.utilization_out_pct, **error_deltas)
            evaluate_interface_alerts(interface, telemetry)
            if previous_oper_status != interface.oper_status:
                interface_events.append({"event": "interface.status.changed", "id": interface.id, "device_id": device.id, "site_id": device.site_id, "oper_status": interface.oper_status})
        evaluate_device_alerts(device, result, previous_status)
        transaction.on_commit(lambda: broadcast_device({"event": "device.telemetry.updated", "id": device.id, "site_id": device.site_id, "status": device.status, "latency_ms": device.last_latency_ms, "packet_loss_pct": device.current_packet_loss, "status_changed": previous_status != device.status}))
        for event in interface_events:
            transaction.on_commit(lambda payload=event: broadcast_device(payload))
        return device
