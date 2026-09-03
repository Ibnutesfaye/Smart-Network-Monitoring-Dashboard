from rest_framework.routers import DefaultRouter

from .views import AlertRuleViewSet, AlertViewSet

router = DefaultRouter()
router.register("", AlertViewSet, basename="alerts")
router.register("rules", AlertRuleViewSet, basename="alert-rules")

urlpatterns = router.urls
