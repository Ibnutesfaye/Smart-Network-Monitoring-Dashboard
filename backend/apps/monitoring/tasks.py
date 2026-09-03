from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.alerts.models import Alert, AlertRule
from apps.alerts.services import create_alert
from apps.devices.models import Device, DeviceTelemetry, InterfaceTelemetry, NetworkSegment
from apps.traffic.models import TrafficSample

from .authorization import UnauthorizedTarget, parse_authorized_network
from .broadcast import broadcast_dashboard, broadcast_device, broadcast_traffic
from .collectors import get_collector
from .processing import process_monitoring_result
from .services import get_monitor


@shared_task
def discover_devices():
    monitor = get_monitor()
    if settings.MONITORING_MODE == "mock":
        cidrs = [settings.SUBNET_CIDR]
    else:
        cidrs = list(NetworkSegment.objects.filter(active=True, discovery_enabled=True, monitoring_enabled=True).values_list("cidr", flat=True)[: settings.DISCOVERY_MAX_SEGMENTS_PER_RUN])
    discovered = []
    for cidr in cidrs:
        try:
            parse_authorized_network(cidr)
        except UnauthorizedTarget:
            continue
        discovered.extend(monitor.discover_devices(cidr))
    known_ips = set(Device.objects.values_list("ip_address", flat=True))
    for dto in discovered:
        device, created = Device.objects.update_or_create(
            ip_address=dto.ip_address,
            defaults={
                "device_name": dto.device_name,
                "hostname": dto.hostname,
                "mac_address": dto.mac_address,
                "vendor": dto.vendor,
                "status": dto.status if dto.status != "unknown" else Device.Status.UNKNOWN,
                "last_seen": timezone.now(),
            },
        )
        if created and dto.ip_address not in known_ips:
            device.is_known = False
            device.save(update_fields=["is_known"])
            create_alert(
                device,
                Alert.AlertType.UNKNOWN_DEVICE,
                Alert.Level.MEDIUM,
                f"Unknown device detected: {dto.device_name} ({dto.ip_address})",
            )
        broadcast_device(
            {
                "id": device.id,
                "device_name": device.device_name,
                "status": device.status,
                "ip_address": str(device.ip_address),
                "site_id": device.site_id,
            }
        )


@shared_task
def check_device_status():
    return monitor_active_devices()


@shared_task(autoretry_for=(ConnectionError,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def monitor_device(device_id):
    device = Device.objects.select_related("site").get(pk=device_id)
    result = get_collector().collect_device(device)
    process_monitoring_result(device_id, result)


@shared_task
def monitor_active_devices():
    device_ids = Device.objects.filter(monitoring_enabled=True).values_list("id", flat=True).iterator(chunk_size=100)
    for device_id in device_ids:
        monitor_device.delay(device_id)


@shared_task
def sample_traffic():
    monitor = get_monitor()
    traffic = monitor.collect_traffic()
    sample = TrafficSample.objects.create(
        device=None,
        upload_speed=traffic.upload_speed,
        download_speed=traffic.download_speed,
        bandwidth_usage=traffic.bandwidth_usage,
    )
    broadcast_traffic(
        {
            "upload": sample.upload_speed,
            "download": sample.download_speed,
            "bandwidth": sample.bandwidth_usage,
            "timestamp": sample.timestamp.isoformat(),
        }
    )
    from apps.analytics.risk import calculate_health_score

    broadcast_dashboard(
        {
            "health_score": calculate_health_score(),
            "traffic": {
                "upload": sample.upload_speed,
                "download": sample.download_speed,
            },
        }
    )


@shared_task
def evaluate_alert_rules():
    rules = AlertRule.objects.filter(is_active=True)
    for rule in rules:
        if rule.bandwidth_threshold_mbps:
            latest = TrafficSample.objects.filter(device__isnull=True).first()
            if latest and latest.bandwidth_usage > rule.bandwidth_threshold_mbps:
                if not Alert.objects.filter(
                    alert_type=Alert.AlertType.HIGH_BANDWIDTH,
                    created_at__gte=timezone.now() - timedelta(minutes=5),
                ).exists():
                    create_alert(
                        None,
                        Alert.AlertType.HIGH_BANDWIDTH,
                        rule.alert_level,
                        f"Bandwidth {latest.bandwidth_usage} Mbps exceeds threshold {rule.bandwidth_threshold_mbps} Mbps",
                    )


@shared_task
def cleanup_old_traffic():
    cutoff = timezone.now() - timedelta(days=90)
    TrafficSample.objects.filter(timestamp__lt=cutoff).delete()


@shared_task
def cleanup_old_telemetry():
    cutoff = timezone.now() - timedelta(days=settings.TELEMETRY_RETENTION_DAYS)
    total = 0
    for model in (DeviceTelemetry, InterfaceTelemetry):
        while True:
            ids = list(model.objects.filter(timestamp__lt=cutoff).values_list("id", flat=True)[: settings.TELEMETRY_CLEANUP_BATCH_SIZE])
            if not ids:
                break
            deleted, _ = model.objects.filter(id__in=ids).delete()
            total += deleted
    return total
