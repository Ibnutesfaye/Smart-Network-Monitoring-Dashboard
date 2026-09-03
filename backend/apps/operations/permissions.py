from rest_framework.permissions import BasePermission, SAFE_METHODS


def allowed_site_ids(user):
    if user.is_superuser or getattr(user, "is_administrator", False):
        return None
    return set(user.sites.values_list("id", flat=True))


class IsOperator(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in {"administrator", "network_analyst"})


class IsAdministratorOrScopedReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.method in SAFE_METHODS or request.user.role == "administrator"
