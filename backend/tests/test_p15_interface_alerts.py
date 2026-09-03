import pytest

from apps.alerts.engine import evaluate_interface_alerts
from apps.alerts.models import Alert, AlertRule
from apps.devices.models import Device, DeviceInterface, InterfaceTelemetry


@pytest.fixture
def interface():
    device = Device.objects.create(device_name="switch", ip_address="10.20.0.1")
    return DeviceInterface.objects.create(device=device, if_index=1, name="uplink", admin_status="up", oper_status="up", speed_bps=1_000_000_000)


def sample(interface, **values):
    defaults = {"interface": interface, "utilization_in_pct": None, "utilization_out_pct": None, "inbound_errors_delta": None, "outbound_errors_delta": None, "inbound_discards_delta": None, "outbound_discards_delta": None}
    defaults.update(values)
    return InterfaceTelemetry(**defaults)


@pytest.mark.django_db
def test_interface_down_pending_dedup_and_recovery(interface):
    AlertRule.objects.create(name="Unexpected down", alert_type=Alert.AlertType.INTERFACE_DOWN, alert_level=Alert.Level.HIGH, consecutive_samples=2, recovery_samples=2)
    interface.oper_status = "down"
    interface.save()
    evaluate_interface_alerts(interface, sample(interface))
    alert = Alert.objects.get(interface=interface)
    assert alert.state == Alert.State.PENDING
    evaluate_interface_alerts(interface, sample(interface))
    alert.refresh_from_db()
    assert alert.state == Alert.State.FIRING and alert.occurrence_count == 2
    assert Alert.objects.filter(interface=interface).count() == 1
    interface.oper_status = "up"
    interface.save()
    evaluate_interface_alerts(interface, sample(interface))
    alert.refresh_from_db()
    assert alert.state == Alert.State.FIRING
    evaluate_interface_alerts(interface, sample(interface))
    alert.refresh_from_db()
    assert alert.state == Alert.State.RESOLVED


@pytest.mark.django_db
def test_admin_disabled_interface_does_not_fire_by_default(interface):
    AlertRule.objects.create(name="Down", alert_type=Alert.AlertType.INTERFACE_DOWN, alert_level=Alert.Level.HIGH)
    interface.admin_status = "down"
    interface.oper_status = "down"
    interface.save()
    evaluate_interface_alerts(interface, sample(interface))
    assert not Alert.objects.filter(interface=interface).exists()


@pytest.mark.django_db
def test_utilization_uses_telemetry_unknown_dedup_and_recovery(interface):
    AlertRule.objects.create(name="Utilization", alert_type=Alert.AlertType.HIGH_INTERFACE_UTILIZATION, alert_level=Alert.Level.HIGH, threshold=80, consecutive_samples=2, recovery_samples=1)
    evaluate_interface_alerts(interface, sample(interface))
    assert not Alert.objects.filter(interface=interface).exists()
    high = sample(interface, utilization_in_pct=81, utilization_out_pct=90)
    evaluate_interface_alerts(interface, high)
    evaluate_interface_alerts(interface, high)
    alert = Alert.objects.get(interface=interface)
    assert alert.state == Alert.State.FIRING and alert.occurrence_count == 2
    evaluate_interface_alerts(interface, sample(interface, utilization_in_pct=20, utilization_out_pct=30))
    alert.refresh_from_db()
    assert alert.state == Alert.State.RESOLVED


@pytest.mark.django_db
def test_interface_errors_use_recent_deltas_not_lifetime_counters(interface):
    AlertRule.objects.create(name="Errors", alert_type=Alert.AlertType.INTERFACE_ERRORS, alert_level=Alert.Level.HIGH, threshold=5, consecutive_samples=2, recovery_samples=1)
    interface.inbound_errors = 9_000_000
    interface.save()
    rising = sample(interface, inbound_errors_delta=4, outbound_errors_delta=3)
    evaluate_interface_alerts(interface, rising)
    evaluate_interface_alerts(interface, rising)
    alert = Alert.objects.get(interface=interface)
    assert alert.state == Alert.State.FIRING and alert.occurrence_count == 2
    evaluate_interface_alerts(interface, sample(interface, inbound_errors_delta=0, outbound_errors_delta=0))
    alert.refresh_from_db()
    assert alert.state == Alert.State.RESOLVED
