def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_activity(user, action, description, request=None):
    from .models import ActivityLog

    ip = get_client_ip(request) if request else None
    ActivityLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        description=description,
        ip_address=ip,
    )
