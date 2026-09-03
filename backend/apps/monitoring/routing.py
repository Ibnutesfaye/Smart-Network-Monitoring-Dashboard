from django.urls import path

from .consumers import AlertConsumer, DashboardConsumer, DeviceConsumer

websocket_urlpatterns = [
    path("ws/dashboard/", DashboardConsumer.as_asgi()),
    path("ws/devices/", DeviceConsumer.as_asgi()),
    path("ws/alerts/", AlertConsumer.as_asgi()),
]
