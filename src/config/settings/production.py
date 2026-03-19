import sentry_sdk

from .base import *  # noqa
from .base import env

SESSION_COOKIE_AGE = 60 * 60 * 4  # 4 hours

SESSION_COOKIE_SECURE = True

SECURE_SSL_REDIRECT = True

CSRF_COOKIE_SECURE = True

SECURE_BROWSER_XSS_FILTER = True

SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = ["localhost"] + env.list("ALLOWED_HOST")

ADMINS = [el.split(":") for el in env.list("DJANGO_ADMINS", default=[])]

USE_BREVO = env.bool("USE_BREVO", default=False)

EMAIL_BACKEND = (
    "anymail.backends.sendinblue.EmailBackend" if USE_BREVO else "django.core.mail.backends.smtp.EmailBackend"
)
ANYMAIL = {"SENDINBLUE_API_KEY": env("SENDINBLUE_API_KEY")}
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# Celery config
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_BROKER_URL")

DEFENDER_BEHIND_REVERSE_PROXY = True

OTP_EMAIL_TOKEN_VALIDITY = env("OTP_EMAIL_TOKEN_VALIDITY", default=600)

SENTRY_URL = env("SENTRY_URL")

sentry_sdk.init(SENTRY_URL, traces_sample_rate=1.0)

DJANGO_VITE = {"default": {"dev_mode": False, "static_url_prefix": "ui_app_ts/dist"}}
