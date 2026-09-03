from rest_framework.routers import DefaultRouter

from .views import (
    DeviceInterfaceViewSet,
    NetworkSegmentViewSet,
    OrganizationViewSet,
    SiteViewSet,
)

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organizations")
router.register("sites", SiteViewSet, basename="sites")
router.register("network-segments", NetworkSegmentViewSet, basename="network-segments")
router.register("interfaces", DeviceInterfaceViewSet, basename="interfaces")

urlpatterns = router.urls
