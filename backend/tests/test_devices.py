import pytest


@pytest.mark.django_db
def test_device_crud(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    payload = {
        "device_name": "Test Device",
        "hostname": "test",
        "ip_address": "10.0.0.99",
        "mac_address": "00:11:22:33:44:55",
        "vendor": "TestVendor",
    }
    create = api_client.post("/api/v1/devices/", payload)
    assert create.status_code == 201
    device_id = create.data["id"]
    get_resp = api_client.get(f"/api/v1/devices/{device_id}/")
    assert get_resp.status_code == 200
    assert get_resp.data["device_name"] == "Test Device"
