from django.contrib import admin

from .models import Device, DeviceInterface, DeviceStatusHistory, NetworkSegment, Organization, Site

admin.site.register(Organization)
admin.site.register(Site)
admin.site.register(NetworkSegment)
admin.site.register(DeviceInterface)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("device_name", "ip_address", "status", "vendor", "last_seen")
    list_filter = ("status", "is_known")
    search_fields = ("device_name", "ip_address", "mac_address")


@admin.register(DeviceStatusHistory)
class DeviceStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("device", "status", "latency_ms", "recorded_at")
    list_filter = ("status",)
