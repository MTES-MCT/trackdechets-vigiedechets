import socket

from .base import *  # noqa

SECRET_KEY = "xyzabcdefghu"

INSTALLED_APPS += [  # noqa F405
    "whitenoise.runserver_nostatic",
    "debug_toolbar",
    "django_extensions",
]

ALLOWED_HOSTS = ["*"]

# Configure internal IPs for debug toolbar to work with Docker environment
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[:-1] + '1' for ip in ips] + ['127.0.0.1']

MIDDLEWARE = (
    MIDDLEWARE[:1]  # noqa
    + [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ]
    + MIDDLEWARE[1:]  # noqa
)

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
