from django.urls import path

from .views import DeviceTelemetryView, InterfaceTelemetryView

urlpatterns = [
    path("devices/<int:pk>/", DeviceTelemetryView.as_view(), name="device-telemetry"),
    path("interfaces/<int:pk>/", InterfaceTelemetryView.as_view(), name="interface-telemetry"),
]
