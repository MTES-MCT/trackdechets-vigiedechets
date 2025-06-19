from .base import *  # noqa

SECRET_KEY = "xyzabcdefghu"

INSTALLED_APPS += [  # noqa F405
    "whitenoise.runserver_nostatic",
    "debug_toolbar",
    "django_extensions",
]

ALLOWED_HOSTS = ["*"]

INTERNAL_IPS = [
    "127.0.0.1",
]

MIDDLEWARE = (
        MIDDLEWARE[:1]  # noqa
        + [
            "debug_toolbar.middleware.DebugToolbarMiddleware",
        ]
        + MIDDLEWARE[1:]  # noqa
)

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK" :'common.toolbar.do_show_toolbar'
}
# Celery config
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis"

OTP_EMAIL_TOKEN_VALIDITY = 600

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "mozilla_django_oidc": {"handlers": ["console"], "level": "DEBUG"},
    },
}

DJANGO_VITE = {"default": {"dev_mode": True}}
