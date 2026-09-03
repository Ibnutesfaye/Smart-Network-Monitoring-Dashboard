from .base import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

CELERY_TASK_ALWAYS_EAGER = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

SIMPLE_JWT["ROTATE_REFRESH_TOKENS"] = False  # noqa: F405
SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] = False  # noqa: F405
