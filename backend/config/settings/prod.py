import ipaddress

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
WEBSOCKET_ALLOW_QUERY_AUTH = False


def _require_production_configuration():
    errors = []
    secret = os.getenv("SECRET_KEY", "")  # noqa: F405
    if len(secret) < 50 or secret.startswith(("change-me", "django-insecure")):
        errors.append("SECRET_KEY must be a unique value of at least 50 characters")
    if DEBUG:  # noqa: F405
        errors.append("DEBUG must be False")
    if not ALLOWED_HOSTS or any(host in {"*", "localhost", "127.0.0.1"} for host in ALLOWED_HOSTS):  # noqa: F405
        errors.append("ALLOWED_HOSTS must contain explicit production hostnames")
    if not CORS_ALLOWED_ORIGINS or any("localhost" in origin or "127.0.0.1" in origin for origin in CORS_ALLOWED_ORIGINS):  # noqa: F405
        errors.append("CORS_ORIGINS must contain explicit production HTTPS origins")
    if any(not origin.startswith("https://") for origin in CORS_ALLOWED_ORIGINS):  # noqa: F405
        errors.append("all production CORS origins must use HTTPS")
    db_password = os.getenv("DB_PASSWORD", "")  # noqa: F405
    if not db_password or db_password in {"postgres", "change-me"}:
        errors.append("DB_PASSWORD must be set to a non-default value")
    redis_url = os.getenv("REDIS_URL", "")  # noqa: F405
    if not redis_url.startswith(("redis://", "rediss://")):
        errors.append("REDIS_URL must be configured")
    if MONITORING_MODE not in {"mock", "real"}:  # noqa: F405
        errors.append("MONITORING_MODE must be 'mock' or 'real'")
    try:
        network = ipaddress.ip_network(SUBNET_CIDR, strict=False)  # noqa: F405
        if MONITORING_MODE == "real" and not network.is_private:  # noqa: F405
            errors.append("real monitoring requires a private authorized SUBNET_CIDR")
    except ValueError:
        errors.append("SUBNET_CIDR must be a valid CIDR network")
    if errors:
        raise ImproperlyConfigured("Unsafe production configuration: " + "; ".join(errors))


_require_production_configuration()
