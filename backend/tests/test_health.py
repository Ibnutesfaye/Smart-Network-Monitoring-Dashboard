from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_liveness_is_public():
    response = APIClient().get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
@patch("config.health.Redis.from_url")
def test_readiness_checks_database_and_redis(redis_factory):
    redis_factory.return_value.ping.return_value = True
    response = APIClient().get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": True, "redis": True},
    }
