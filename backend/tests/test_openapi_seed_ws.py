import pytest
from channels.testing import WebsocketCommunicator
from django.core.management import call_command

from apps.alerts.models import Alert
from apps.devices.models import Device
from apps.traffic.models import TrafficSample
from config.asgi import application as asgi_app
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.mark.django_db
def test_openapi_schema_available(api_client):
    # Spectacular swagger UI endpoint (public)
    resp = api_client.get("/api/schema/swagger/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_seed_demo_populates_data():
    call_command("seed_demo", "--noinput")

    assert User.objects.filter(username="admin").exists()
    assert User.objects.filter(username="analyst").exists()

    assert Device.objects.count() >= 1
    assert TrafficSample.objects.count() >= 1
    assert Alert.objects.count() >= 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_websocket_jwt_auth_allows_admin(admin_access_token):
    communicator = WebsocketCommunicator(
        asgi_app, f"/ws/dashboard/?token={admin_access_token}"
    )
    connected, _ = await communicator.connect()
    assert connected is True
    await communicator.disconnect()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_websocket_jwt_auth_rejects_invalid_token():
    communicator = WebsocketCommunicator(asgi_app, "/ws/dashboard/?token=invalid")
    connected, _ = await communicator.connect()
    assert connected is False

