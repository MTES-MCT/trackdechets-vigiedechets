from .base import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "vigiedechets_test",
        "USER": "postgres",
        "PASSWORD": "admin",
        "HOST": "localhost",
        "PORT": 5432,
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # faster hashes

SECRET_KEY = "xyz12345"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

MESSAGE_RECIPIENTS = ["lorem@ipsum.lol"]

OTP_EMAIL_TOKEN_VALIDITY = 600

CSRF_TRUSTED_ORIGINS = ["http://url.test"]

# circumnvent defender when testing
DEFENDER_DISABLE_IP_LOCKOUT = True
DEFENDER_DISABLE_USERNAME_LOCKOUT = True

TD_API_URL = "https://testapi.test"
TD_API_TOKEN = "thetoken"

OIDC_RP_CLIENT_SECRET = "azer"
MONAIOT_OIDC_OP_SERVER_URL = "https://monaiot.test/auth/realms/MonAIOT-integration/protocol/openid-connect"
MONAIOT_OIDC_OP_AUTHORIZATION_ENDPOINT = f"{MONAIOT_OIDC_OP_SERVER_URL}/auth"
MONAIOT_OIDC_OP_TOKEN_ENDPOINT = f"{MONAIOT_OIDC_OP_SERVER_URL}/token"
MONAIOT_OIDC_OP_USER_ENDPOINT = f"{MONAIOT_OIDC_OP_SERVER_URL}/userinfo"
MONAIOT_OIDC_OP_JWKS_ENDPOINT = f"{MONAIOT_OIDC_OP_SERVER_URL}/certs"

PROCONNECT_OIDC_OP_SERVER_URL = "https://proconnect.test"
PROCONNECT_OIDC_OP_AUTHORIZATION_ENDPOINT = f"{PROCONNECT_OIDC_OP_SERVER_URL}/api/v2/authorize"
PROCONNECT_OIDC_OP_TOKEN_ENDPOINT = f"{PROCONNECT_OIDC_OP_SERVER_URL}/api/v2/token"
PROCONNECT_OIDC_OP_USER_ENDPOINT = f"{PROCONNECT_OIDC_OP_SERVER_URL}/api/v2/userinfo"
PROCONNECT_OIDC_OP_JWKS_ENDPOINT = f"{PROCONNECT_OIDC_OP_SERVER_URL}/api/v2/jwks"

ID_ID_CURRASSO = "currasso-idp"
PROCONNECT_ALLOWED_IDP_IDS = [
    ID_ID_CURRASSO,
]

DJANGO_VITE = {"default": {"dev_mode": True}}
SKIP_SIRET_CHECK = True

ALLOWED_USER_FOR_SENTINEL = ["allowed_for_sentinel@mail.test"]
ALLOWED_CATEGORIES_FOR_SENTINEL = ["GENDARMERIE", "INSPECTEUR_ICPE", "OBSERVATOIRE"]
ALLOWED_EMAILS_FOR_DATA_EXPORT = ["allowed_for_data_export@mail.test"]

SKIP_ROAD_CONTROL_SIRET_CHECK = True

SUPPORT_FORM_RECIPIENT = "help@support.test"
