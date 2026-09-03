import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-key-change-in-production")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "channels",
    "apps.accounts",
    "apps.devices",
    "apps.traffic",
    "apps.alerts",
    "apps.reports",
    "apps.analytics",
    "apps.topology",
    "apps.monitoring",
    "apps.audit",
    "apps.operations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.ActivityLogMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_USER_MODEL = "accounts.User"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "snmadmdcp"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "config.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_MINUTES", "15"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("JWT_REFRESH_DAYS", "7"))
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SNMADMDCP API",
    "DESCRIPTION": "Smart Network Monitoring and Device Management Dashboard API",
    "VERSION": "1.0.0",
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://localhost:6379/0")],
        },
    },
}

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

MONITORING_MODE = os.getenv("MONITORING_MODE", "mock")
SUBNET_CIDR = os.getenv("SUBNET_CIDR", "192.168.1.0/24")
WEBSOCKET_ALLOW_QUERY_AUTH = os.getenv("WEBSOCKET_ALLOW_QUERY_AUTH", "True").lower() == "true"
DISCOVERY_MAX_HOSTS = int(os.getenv("DISCOVERY_MAX_HOSTS", "256"))
DISCOVERY_BATCH_SIZE = max(1, min(int(os.getenv("DISCOVERY_BATCH_SIZE", "32")), 256))
DISCOVERY_MAX_SEGMENTS_PER_RUN = max(1, min(int(os.getenv("DISCOVERY_MAX_SEGMENTS_PER_RUN", "20")), 100))
MONITOR_FAILURE_THRESHOLD = int(os.getenv("MONITOR_FAILURE_THRESHOLD", "3"))
MONITOR_RECOVERY_THRESHOLD = int(os.getenv("MONITOR_RECOVERY_THRESHOLD", "2"))
MONITOR_PING_TIMEOUT_MS = int(os.getenv("MONITOR_PING_TIMEOUT_MS", "1000"))
MONITOR_PING_ATTEMPTS = max(1, min(int(os.getenv("MONITOR_PING_ATTEMPTS", "3")), 10))
TELEMETRY_RETENTION_DAYS = int(os.getenv("TELEMETRY_RETENTION_DAYS", "30"))
TELEMETRY_CLEANUP_BATCH_SIZE = int(os.getenv("TELEMETRY_CLEANUP_BATCH_SIZE", "5000"))
SNMP_TIMEOUT_SECONDS = max(0.2, float(os.getenv("SNMP_TIMEOUT_SECONDS", "2")))
SNMP_RETRIES = max(0, min(int(os.getenv("SNMP_RETRIES", "1")), 3))
SNMP_COMMUNITY = os.getenv("SNMP_COMMUNITY", "")
SNMP_V3_USERNAME = os.getenv("SNMP_V3_USERNAME", "")
SNMP_V3_AUTH_KEY = os.getenv("SNMP_V3_AUTH_KEY", "")
SNMP_V3_PRIV_KEY = os.getenv("SNMP_V3_PRIV_KEY", "")
SNMP_V3_SECURITY_LEVEL = os.getenv("SNMP_V3_SECURITY_LEVEL", "authPriv")
SNMP_V3_AUTH_PROTOCOL = os.getenv("SNMP_V3_AUTH_PROTOCOL", "SHA256")
SNMP_V3_PRIV_PROTOCOL = os.getenv("SNMP_V3_PRIV_PROTOCOL", "AES128")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@snmadmdcp.local")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
THREAT_INTEL_API_KEY = os.getenv("THREAT_INTEL_API_KEY", "")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
