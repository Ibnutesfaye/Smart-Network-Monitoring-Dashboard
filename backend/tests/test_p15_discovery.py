from unittest.mock import Mock, patch

import pytest
from django.test import override_settings

from apps.devices.models import NetworkSegment, Organization, Site
from apps.monitoring.authorization import UnauthorizedTarget, parse_authorized_network
from apps.monitoring.tasks import discover_devices


@pytest.mark.django_db
@override_settings(MONITORING_MODE="real", DISCOVERY_MAX_HOSTS=256)
@patch("apps.monitoring.tasks.get_monitor")
def test_discovery_uses_only_enabled_authorized_segments(get_monitor):
    organization = Organization.objects.create(name="Org", code="org-discovery")
    site = Site.objects.create(organization=organization, name="HQ", code="hq")
    NetworkSegment.objects.create(site=site, name="enabled", cidr="10.30.0.0/24", discovery_enabled=True)
    NetworkSegment.objects.create(site=site, name="disabled", cidr="10.31.0.0/24", discovery_enabled=False)
    monitor = Mock()
    monitor.discover_devices.return_value = []
    get_monitor.return_value = monitor
    discover_devices()
    monitor.discover_devices.assert_called_once_with("10.30.0.0/24")


@override_settings(DISCOVERY_MAX_HOSTS=256)
def test_discovery_rejects_default_routes_and_large_networks():
    for cidr in ("0.0.0.0/0", "::/0", "10.0.0.0/8", "invalid"):
        with pytest.raises(UnauthorizedTarget):
            parse_authorized_network(cidr)
