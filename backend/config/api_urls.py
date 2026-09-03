from django.urls import include, path

urlpatterns = [
    path("", include("apps.devices.infrastructure_urls")),
    path("auth/", include("apps.accounts.urls")),
    path("users/", include("apps.accounts.user_urls")),
    path("devices/", include("apps.devices.urls")),
    path("traffic/", include("apps.traffic.urls")),
    path("alerts/", include("apps.alerts.urls")),
    path("reports/", include("apps.reports.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("dashboard/", include("apps.analytics.dashboard_urls")),
    path("topology/", include("apps.topology.urls")),
    path("activity-logs/", include("apps.audit.urls")),
    path("telemetry/", include("apps.monitoring.urls")),
    path("", include("apps.operations.urls")),
]
