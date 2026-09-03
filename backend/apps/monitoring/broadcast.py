from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone


def _send(group, event_type, data):
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            group,
            {"type": event_type, "data": data},
        )


def broadcast_dashboard(metrics):
    _send("dashboard", "dashboard_update", metrics)


def broadcast_device(device_data):
    _send("devices", "device_update", device_data)
    if device_data.get("site_id"):
        _send(f"site_{device_data['site_id']}_devices", "device_update", device_data)


def broadcast_traffic(traffic_data):
    _send("dashboard", "traffic_update", traffic_data)


def broadcast_alert(alert, event="alert.fired"):
    from apps.alerts.serializers import AlertSerializer

    data = AlertSerializer(alert).data
    data["event"] = event
    _send("alerts", "alert_created", data)
    _send("dashboard", "alert_created", data)
    if alert.device_id and alert.device.site_id:
        _send(f"site_{alert.device.site_id}_alerts", "alert_created", data)
        _send(f"site_{alert.device.site_id}_dashboard", "alert_created", data)


def broadcast_operational_event(event, obj):
    data = {"id": obj.pk}
    for field in ("incident_number", "title", "status", "site_id", "start_at", "end_at"):
        if hasattr(obj, field):
            value = getattr(obj, field)
            data[field] = value.isoformat() if hasattr(value, "isoformat") else value
    envelope = {"version": 1, "type": event, "timestamp": timezone.now().isoformat(), "data": data}
    _send("dashboard", "operational_event", envelope)
    site_ids = {data["site_id"]} if data.get("site_id") else set()
    if hasattr(obj, "sites"):
        site_ids.update(obj.sites.values_list("id", flat=True))
    if hasattr(obj, "devices"):
        site_ids.update(obj.devices.exclude(site_id__isnull=True).values_list("site_id", flat=True))
    if hasattr(obj, "interfaces"):
        site_ids.update(obj.interfaces.exclude(device__site_id__isnull=True).values_list("device__site_id", flat=True))
    data["site_ids"] = sorted(site_ids)
    for site_id in site_ids:
        _send(f"site_{site_id}_dashboard", "operational_event", envelope)
