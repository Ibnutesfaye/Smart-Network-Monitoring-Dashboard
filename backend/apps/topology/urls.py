from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import TopologyLinkViewSet, TopologyView

router = DefaultRouter()
router.register("links", TopologyLinkViewSet, basename="topology-link")

urlpatterns = [
    path("", TopologyView.as_view(), name="topology"),
    *router.urls,
]
