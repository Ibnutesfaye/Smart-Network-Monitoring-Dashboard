import pytest


@pytest.mark.django_db
def test_login(api_client, admin_user):
    url = "/api/v1/auth/login/"
    response = api_client.post(url, {"username": "testadmin", "password": "testpass123"})
    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_users_list_requires_admin(api_client, admin_user, analyst_user):
    api_client.force_authenticate(user=analyst_user)
    response = api_client.get("/api/v1/users/")
    assert response.status_code == 403

    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/users/")
    assert response.status_code == 200
