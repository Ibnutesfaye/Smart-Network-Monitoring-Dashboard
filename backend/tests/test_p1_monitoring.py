from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.utils import timezone

from apps.alerts.engine import fire_or_update
from apps.alerts.models import Alert, AlertRule
from apps.devices.models import Device, NetworkSegment, Organization, Site
from apps.monitoring.authorization import is_authorized_target
from apps.monitoring.collectors.base import MonitoringResult
from apps.monitoring.collectors.mock import MockCollector
from apps.monitoring.collectors.ping import PingCollector
from apps.monitoring.processing import (
    calculate_counter_rates,
    counter_delta,
    process_monitoring_result,
    utilization,
)


@pytest.fixture
def network():
    organization = Organization.objects.create(name="Example", code="example")
    site = Site.objects.create(organization=organization, name="HQ", code="hq")
    segment = NetworkSegment.objects.create(site=site, name="LAN", cidr="10.10.0.0/24", discovery_enabled=True)
    return site, segment


@pytest.mark.django_db
def test_cidr_validation_and_authorization(network):
    site, _ = network
    with override_settings(MONITORING_MODE="real", DISCOVERY_MAX_HOSTS=256):
        assert is_authorized_target("10.10.0.5", site)
        assert not is_authorized_target("10.11.0.5", site)


@pytest.mark.django_db
def test_default_route_is_rejected(network):
    _, segment = network
    segment.cidr = "0.0.0.0/0"
    with pytest.raises(ValidationError):
        segment.full_clean()



@pytest.mark.django_db
@override_settings(MONITORING_MODE="mock", MONITOR_FAILURE_THRESHOLD=3, MONITOR_RECOVERY_THRESHOLD=2)
def test_availability_threshold_and_recovery(network):
    site, segment = network
    device = Device.objects.create(device_name="router", ip_address="10.10.0.1", site=site, network_segment=segment, status=Device.Status.ONLINE)
    base = timezone.now()
    for offset in range(2):
        process_monitoring_result(device.id, MonitoringResult(reachable=False, packet_loss_pct=100, source="test", collected_at=base + timedelta(seconds=offset)))
    device.refresh_from_db()
    assert device.status == Device.Status.DEGRADED
    process_monitoring_result(device.id, MonitoringResult(reachable=False, packet_loss_pct=100, source="test", collected_at=base + timedelta(seconds=3)))
    device.refresh_from_db()
    assert device.status == Device.Status.OFFLINE
    assert Alert.objects.filter(device=device, alert_type=Alert.AlertType.DEVICE_OFFLINE).count() == 1
    for offset in (4, 5):
        process_monitoring_result(device.id, MonitoringResult(reachable=True, latency_ms=5, packet_loss_pct=0, source="test", collected_at=base + timedelta(seconds=offset)))
    device.refresh_from_db()
    assert device.status == Device.Status.ONLINE
    assert Alert.objects.filter(device=device, alert_type=Alert.AlertType.DEVICE_OFFLINE, state=Alert.State.RESOLVED).exists()


@pytest.mark.django_db
def test_mock_collector_is_deterministic(network):
    site, segment = network
    device = Device.objects.create(device_name="switch", ip_address="10.10.0.2", site=site, network_segment=segment)
    assert MockCollector().collect_device(device) == MockCollector().collect_device(device)


@pytest.mark.django_db
@override_settings(MONITORING_MODE="real", MONITOR_PING_ATTEMPTS=2, MONITOR_PING_TIMEOUT_MS=1000, DISCOVERY_MAX_HOSTS=256)
@patch("apps.monitoring.collectors.ping.subprocess.run")
def test_ping_collector_parses_without_shell(run, network):
    site, segment = network
    device = Device.objects.create(device_name="host", ip_address="10.10.0.9", site=site, network_segment=segment)
    run.return_value = Mock(returncode=0, stdout="Reply time=10ms\nReply time=20ms")
    result = PingCollector().collect_device(device)
    assert result.reachable and result.latency_ms == 15
    assert isinstance(run.call_args.args[0], list)


def test_counter_calculation_edges():
    assert calculate_counter_rates(None, 20, 1) is None
    assert calculate_counter_rates(20, 10, 1) is None
    assert calculate_counter_rates(10, 20, 0) is None
    assert calculate_counter_rates(100, 200, 2) == 400
    assert utilization(500_000_000, 1_000_000_000) == 50
    assert counter_delta(None, 10) is None
    assert counter_delta(20, 10) is None
    assert counter_delta(10, 20) == 10


@pytest.mark.django_db
def test_alert_pending_firing_and_deduplication(network):
    site, segment = network
    device = Device.objects.create(device_name="core", ip_address="10.10.0.3", site=site, network_segment=segment)
    rule = AlertRule.objects.create(name="Latency", alert_type=Alert.AlertType.HIGH_LATENCY, alert_level=Alert.Level.HIGH, threshold=150, consecutive_samples=3)
    for _ in range(2):
        alert = fire_or_update(device, rule.alert_type, rule.alert_level, "high", rule)
    assert alert.state == Alert.State.PENDING
    alert = fire_or_update(device, rule.alert_type, rule.alert_level, "high", rule)
    assert alert.state == Alert.State.FIRING
    assert alert.occurrence_count == 3
    assert Alert.objects.filter(device=device, alert_type=rule.alert_type).count() == 1
