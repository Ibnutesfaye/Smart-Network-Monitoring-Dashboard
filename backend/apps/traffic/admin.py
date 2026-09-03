from django.contrib import admin

from .models import TrafficSample


@admin.register(TrafficSample)
class TrafficSampleAdmin(admin.ModelAdmin):
    list_display = ("device", "upload_speed", "download_speed", "bandwidth_usage", "timestamp")
    list_filter = ("timestamp",)
