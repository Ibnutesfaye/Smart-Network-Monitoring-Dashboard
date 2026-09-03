import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.devices.models import Device, DeviceTelemetry, NetworkSegment, Organization, Site
from apps.alerts.models import Alert


@pytest.fixture
def authenticated_client():
    user = get_user_model().objects.create_user(username="viewer", password="test-password", role="network_analyst")
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.django_db
def test_device_site_filter_and_bounded_telemetry(authenticated_client):
    organization = Organization.objects.create(name="Org", code="org")
    site = Site.objects.create(organization=organization, name="HQ", code="hq")
    segment = NetworkSegment.objects.create(site=site, name="LAN", cidr="10.0.0.0/24")
    device = Device.objects.create(device_name="edge", ip_address="10.0.0.1", site=site, network_segment=segment)
    DeviceTelemetry.objects.create(device=device, reachable=True, source="test")
    response = authenticated_client.get(f"/api/v1/devices/?site={site.id}")
    assert response.status_code == 200 and response.json()["count"] == 1
    assert authenticated_client.get(f"/api/v1/telemetry/devices/{device.id}/?range=forever").status_code == 400
    assert authenticated_client.get(f"/api/v1/telemetry/devices/{device.id}/?range=1h").status_code == 200


@pytest.mark.django_db
def test_anonymous_p1_api_is_rejected():
    assert APIClient().get("/api/v1/sites/").status_code == 401


@pytest.mark.django_db
def test_alert_acknowledgement_preserves_active_condition(authenticated_client):
    alert = Alert.objects.create(alert_type=Alert.AlertType.HIGH_CPU, alert_level=Alert.Level.HIGH, message="CPU high", state=Alert.State.FIRING)
    response = authenticated_client.patch(f"/api/v1/alerts/{alert.id}/acknowledge/", {"note": "Investigating"}, format="json")
    assert response.status_code == 200
    alert.refresh_from_db()
    assert alert.state == Alert.State.ACKNOWLEDGED
    assert alert.acknowledgement_note == "Investigating"
    assert alert.resolved_at is None
