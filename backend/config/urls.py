from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from config.health import LivenessView, ReadinessView

urlpatterns = [
    path("health/live", LivenessView.as_view(), name="health-live"),
    path("health/ready", ReadinessView.as_view(), name="health-ready"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("config.api_urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
