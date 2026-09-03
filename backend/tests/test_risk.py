import pytest

from apps.analytics.risk import calculate_health_score, calculate_risk_score


@pytest.mark.django_db
def test_risk_scores_empty():
    assert calculate_risk_score() >= 0
    assert calculate_health_score() >= 0
