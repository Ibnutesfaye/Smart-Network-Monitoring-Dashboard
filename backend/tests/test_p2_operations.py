from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient

from apps.alerts.models import Alert
from apps.alerts.services import create_alert
from apps.devices.models import Device, DeviceStatusHistory, Organization, Site
from apps.operations.models import IncidentEvent, MaintenanceWindow
from apps.operations.services import (
    create_incident,
    evaluate_maintenance_windows,
    noc_summary,
    transition_incident,
)
from apps.topology.models import TopologyLink

pytestmark = pytest.mark.django_db


@pytest.fixture
def p2_data():
    user = get_user_model().objects.create_user(username="noc", password="test-pass", role="administrator")
    org = Organization.objects.create(name="Operations", code="ops")
    site = Site.objects.create(organization=org, name="Core", code="core")
    device = Device.objects.create(device_name="core-r1", ip_address="10.20.0.1", site=site, status=Device.Status.OFFLINE)
    return user, site, device


def test_incident_number_alert_link_and_timeline(p2_data):
    user, site, device = p2_data
    alert = Alert.objects.create(device=device, alert_type=Alert.AlertType.DEVICE_OFFLINE, alert_level=Alert.Level.CRITICAL, message="down")
    incident = create_incident({"title": "Core outage", "site": site, "severity": "critical", "priority": "p1"}, user, [alert])
    assert incident.incident_number.startswith(f"INC-{timezone.now():%Y}-")
    assert incident.alerts.get() == alert
    assert list(incident.events.values_list("event_type", flat=True)) == ["created"]


def test_incident_transitions_and_reopen(p2_data):
    user, site, _ = p2_data
    incident = create_incident({"title": "Routing", "site": site}, user)
    transition_incident(incident, "acknowledged", user)
    transition_incident(incident, "investigating", user)
    transition_incident(incident, "resolved", user, "Route restored")
    assert incident.resolved_at and incident.time_to_resolve is not None
    transition_incident(incident, "investigating", user)
    assert incident.resolved_at is None
    with pytest.raises(ValueError):
        transition_incident(incident, "open", user)


def test_maintenance_date_validation_and_idempotent_activation(p2_data):
    user, site, _ = p2_data
    now = timezone.now()
    invalid = MaintenanceWindow(title="bad", start_at=now, end_at=now, created_by=user)
    with pytest.raises(ValidationError):
        invalid.full_clean()
    window = MaintenanceWindow.objects.create(title="change", start_at=now - timedelta(minutes=1), end_at=now + timedelta(hours=1), created_by=user)
    window.sites.add(site)
    assert evaluate_maintenance_windows(now) == (1, 0)
    assert evaluate_maintenance_windows(now) == (0, 0)
    window.refresh_from_db()
    assert window.status == MaintenanceWindow.Status.ACTIVE


def test_active_maintenance_records_and_suppresses_alert(p2_data):
    user, site, device = p2_data
    now = timezone.now()
    window = MaintenanceWindow.objects.create(title="change", status="active", start_at=now - timedelta(minutes=1), end_at=now + timedelta(hours=1), created_by=user)
    window.devices.add(device)
    alert = create_alert(device, Alert.AlertType.DEVICE_OFFLINE, Alert.Level.CRITICAL, "down during maintenance")
    assert alert.maintenance_suppressed is True
    assert alert.maintenance_window == window


def test_noc_summary_formula_and_site_scope(p2_data):
    user, site, device = p2_data
    Alert.objects.create(device=device, alert_type=Alert.AlertType.DEVICE_OFFLINE, alert_level=Alert.Level.CRITICAL, message="down")
    create_incident({"title": "Outage", "site": site}, user)
    result = noc_summary(user)
    assert result["devices"]["down"] == 1
    assert result["health_score"] == 74
    analyst = get_user_model().objects.create_user(username="scoped", password="test-pass", role="network_analyst")
    analyst.sites.add(site)
    assert noc_summary(analyst)["devices"]["total"] == 1


def test_topology_rejects_self_and_reverse_links(p2_data):
    _, site, source = p2_data
    target = Device.objects.create(device_name="core-r2", ip_address="10.20.0.2", site=site)
    with pytest.raises(ValidationError):
        TopologyLink(site=site, source_device=source, target_device=source).full_clean()
    TopologyLink.objects.create(site=site, source_device=source, target_device=target)
    client = APIClient()
    client.force_authenticate(p2_data[0])
    response = client.post("/api/v1/topology/links/", {"site": site.pk, "source_device": target.pk, "target_device": source.pk}, format="json")
    assert response.status_code == 400


def test_incident_api_comments_assignment_and_permissions(p2_data):
    user, site, _ = p2_data
    client = APIClient()
    client.force_authenticate(user)
    created = client.post("/api/v1/incidents/", {"title": "WAN loss", "site": site.pk, "severity": "high", "priority": "p2"}, format="json")
    assert created.status_code == 201
    incident_id = created.data["id"]
    assert client.post(f"/api/v1/incidents/{incident_id}/assign_to_me/").status_code == 200
    assert client.post(f"/api/v1/incidents/{incident_id}/comments/", {"body": "Carrier engaged"}, format="json").status_code == 201
    assert IncidentEvent.objects.filter(incident_id=incident_id, event_type="comment_added").exists()
    anonymous = APIClient()
    assert anonymous.get("/api/v1/incidents/").status_code == 401


def test_cancelled_maintenance_never_activates(p2_data):
    user, site, _ = p2_data
    client = APIClient()
    client.force_authenticate(user)
    now = timezone.now()
    created = client.post("/api/v1/maintenance/", {"title": "Upgrade", "start_at": (now + timedelta(minutes=1)).isoformat(), "end_at": (now + timedelta(hours=1)).isoformat(), "sites": [site.pk]}, format="json")
    assert created.status_code == 201
    assert client.post(f"/api/v1/maintenance/{created.data['id']}/cancel/").status_code == 200
    window = MaintenanceWindow.objects.get(pk=created.data["id"])
    window.start_at = now - timedelta(minutes=1)
    window.save(update_fields=["start_at"])
    evaluate_maintenance_windows(now)
    window.refresh_from_db()
    assert window.status == MaintenanceWindow.Status.CANCELLED


def test_noc_operational_aggregation_endpoints_are_bounded(p2_data):
    user, site, device = p2_data
    DeviceStatusHistory.objects.create(device=device, status=Device.Status.OFFLINE)
    client = APIClient()
    client.force_authenticate(user)
    availability = client.get(f"/api/v1/noc/availability/?range=24h&site={site.pk}")
    traffic = client.get(f"/api/v1/noc/traffic/?site={site.pk}")
    problems = client.get("/api/v1/noc/problems/")
    assert availability.status_code == 200
    assert len(availability.data["results"]) <= 720
    assert traffic.status_code == 200
    assert len(traffic.data["top_interfaces"]) <= 10
    assert problems.status_code == 200
    assert len(problems.data["longest_down"]) <= 10
