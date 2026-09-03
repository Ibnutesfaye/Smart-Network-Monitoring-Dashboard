from django.contrib import admin

from .models import Alert, AlertRule


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("alert_type", "alert_level", "state", "device", "occurrence_count", "created_at")
    list_filter = ("alert_level", "alert_type", "state", "acknowledged")


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "alert_type", "alert_level", "is_active")
