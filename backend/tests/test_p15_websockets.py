from datetime import timedelta

import pytest
from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from apps.devices.models import Organization, Site
from config.asgi import application


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_websocket_subprotocol_auth_and_safe_representative_events(admin_access_token):
    communicator = WebsocketCommunicator(application, "/ws/devices/", subprotocols=["access_token", admin_access_token])
    connected, subprotocol = await communicator.connect()
    assert connected and subprotocol == "access_token"
    layer = get_channel_layer()
    events = [
        {"event": "device.status.changed", "id": 1, "status": "offline"},
        {"event": "device.telemetry.updated", "id": 1, "latency_ms": 12},
        {"event": "interface.status.changed", "id": 2, "oper_status": "down"},
    ]
    for event in events:
        await layer.group_send("devices", {"type": "device_update", "data": event})
        payload = await communicator.receive_json_from()
        assert payload["data"]["event"] == event["event"]
        rendered = str(payload).lower()
        assert all(secret not in rendered for secret in ("community", "auth_key", "priv_key", "password", "authorization"))
    await communicator.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@pytest.mark.parametrize("subprotocols", [None, ["access_token", "malformed"]])
async def test_websocket_rejects_missing_or_malformed_authentication(subprotocols):
    communicator = WebsocketCommunicator(application, "/ws/alerts/", subprotocols=subprotocols)
    connected, _ = await communicator.connect()
    assert not connected


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_websocket_rejects_expired_token(admin_user):
    token = AccessToken.for_user(admin_user)
    token.set_exp(lifetime=timedelta(seconds=-1))
    communicator = WebsocketCommunicator(application, "/ws/dashboard/", subprotocols=["access_token", str(token)])
    connected, _ = await communicator.connect()
    assert not connected


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_alert_events_and_disconnect_cleanup(admin_access_token):
    communicator = WebsocketCommunicator(application, "/ws/alerts/", subprotocols=["access_token", admin_access_token])
    connected, _ = await communicator.connect()
    assert connected
    layer = get_channel_layer()
    for event in ("alert.fired", "alert.acknowledged", "alert.resolved"):
        await layer.group_send("alerts", {"type": "alert_created", "data": {"event": event, "id": 1}})
        payload = await communicator.receive_json_from()
        assert payload["data"]["event"] == event
    await communicator.disconnect()
    await layer.group_send("alerts", {"type": "alert_created", "data": {"event": "alert.fired", "id": 2}})
    assert await communicator.receive_nothing(timeout=0.1)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_site_scoped_websocket_does_not_receive_other_site_events():
    @sync_to_async
    def setup():
        org = Organization.objects.create(name="Scoped org", code="scoped-org")
        allowed = Site.objects.create(organization=org, name="Allowed", code="allowed")
        denied = Site.objects.create(organization=org, name="Denied", code="denied")
        user = get_user_model().objects.create_user(username="scoped-ws", password="test-pass", role="network_analyst")
        user.sites.add(allowed)
        return str(AccessToken.for_user(user)), allowed.pk, denied.pk

    token, allowed_id, denied_id = await setup()
    communicator = WebsocketCommunicator(application, "/ws/dashboard/", subprotocols=["access_token", token])
    connected, _ = await communicator.connect()
    assert connected
    layer = get_channel_layer()
    await layer.group_send(f"site_{denied_id}_dashboard", {"type": "operational_event", "data": {"version": 1, "type": "incident.created", "data": {"site_id": denied_id}}})
    assert await communicator.receive_nothing(timeout=0.1)
    await layer.group_send(f"site_{allowed_id}_dashboard", {"type": "operational_event", "data": {"version": 1, "type": "incident.created", "data": {"site_id": allowed_id}}})
    payload = await communicator.receive_json_from()
    assert payload["data"]["site_id"] == allowed_id
    await communicator.disconnect()
