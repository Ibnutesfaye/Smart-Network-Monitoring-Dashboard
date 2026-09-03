from django.urls import path

from .views import AlertTrendsView, DeviceGrowthView, SecurityStatsView, TrafficTrendsView

urlpatterns = [
    path("device-growth/", DeviceGrowthView.as_view(), name="device-growth"),
    path("traffic-trends/", TrafficTrendsView.as_view(), name="traffic-trends"),
    path("alert-trends/", AlertTrendsView.as_view(), name="alert-trends"),
    path("security-stats/", SecurityStatsView.as_view(), name="security-stats"),
]
