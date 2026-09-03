import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="testadmin",
        email="admin@test.com",
        password="testpass123",
        role="administrator",
    )


@pytest.fixture
def analyst_user(db):
    return User.objects.create_user(
        username="testanalyst",
        email="analyst@test.com",
        password="testpass123",
        role="network_analyst",
    )


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def admin_access_token(admin_user):
    refresh = RefreshToken.for_user(admin_user)
    return str(refresh.access_token)
