from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    IncidentViewSet,
    MaintenanceWindowViewSet,
    NocAvailabilityView,
    NocProblemsView,
    NocSummaryView,
    NocTrafficView,
)

router = DefaultRouter()
router.register("incidents", IncidentViewSet, basename="incident")
router.register("maintenance", MaintenanceWindowViewSet, basename="maintenance")

urlpatterns = [
    path("noc/summary/", NocSummaryView.as_view(), name="noc-summary"),
    path("noc/availability/", NocAvailabilityView.as_view(), name="noc-availability"),
    path("noc/traffic/", NocTrafficView.as_view(), name="noc-traffic"),
    path("noc/problems/", NocProblemsView.as_view(), name="noc-problems"),
    *router.urls,
]
