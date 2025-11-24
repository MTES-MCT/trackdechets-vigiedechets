import datetime as dt

import boto3
import pytest
from django.conf import settings
from django.test.client import Client
from django_otp import DEVICE_ID_SESSION_KEY
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.constants import OIDCTypeChoice, UserCategoryChoice
from accounts.factories import DEFAULT_PASSWORD, ApiUserFactory, EmailDeviceFactory, UserFactory


@pytest.fixture()
def anon_client(db):
    """A Django anonymous client."""
    from django.test.client import Client

    return Client()


@pytest.fixture()
def logged_in_user(db):
    """A Django test client logged in as a base user (second factor not yet performed)."""

    user = UserFactory()

    client = Client()
    client.login(email=user.email, password=DEFAULT_PASSWORD)

    setattr(client, "user", user)
    return client


@pytest.fixture()
def verified_user(logged_in_user):
    """A Django test client (basic user) who completed the second factor."""

    client = logged_in_user

    device = EmailDeviceFactory(user=client.user)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()

    return client


def prepare_verified_client(**user_kwargs):
    user = UserFactory(**user_kwargs)

    client = Client()
    client.login(email=user.email, password=DEFAULT_PASSWORD)
    device = EmailDeviceFactory(user=user)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    setattr(client, "user", user)
    return client


@pytest.fixture
def verified_icpe():
    client = prepare_verified_client(user_category=UserCategoryChoice.INSPECTEUR_ICPE)
    return client


@pytest.fixture()
def verified_ctt():
    client = prepare_verified_client(user_category=UserCategoryChoice.CTT)
    return client


@pytest.fixture()
def verified_inspection_travail():
    client = prepare_verified_client(user_category=UserCategoryChoice.INSPECTEUR_ICPE)
    return client


@pytest.fixture()
def verified_gendarme():
    client = prepare_verified_client(user_category=UserCategoryChoice.GENDARMERIE)

    return client


@pytest.fixture()
def verified_ars():
    client = prepare_verified_client(user_category=UserCategoryChoice.ARS)

    return client


@pytest.fixture()
def verified_douane():
    client = prepare_verified_client(user_category=UserCategoryChoice.DOUANE)
    return client


@pytest.fixture()
def verified_adm_centrale():
    client = prepare_verified_client(user_category=UserCategoryChoice.ADMINISTRATION_CENTRALE)
    return client


@pytest.fixture()
def verified_observatoire():
    client = prepare_verified_client(user_category=UserCategoryChoice.OBSERVATOIRE)

    return client


@pytest.fixture()
def logged_in_staff(db):
    """A Django test client logged in as a staff user."""

    user = UserFactory(is_staff=True)
    client = Client()
    client.login(email=user.email, password=DEFAULT_PASSWORD)

    setattr(client, "user", user)
    return client


@pytest.fixture()
def verified_staff(logged_in_staff):
    """A Django test client (staff) user) who completed the second factor."""

    client = logged_in_staff

    device = EmailDeviceFactory(user=client.user)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()

    return client


@pytest.fixture()
def token_auth_api():
    """Return a DRF api client with token auth credentials"""
    user = ApiUserFactory()
    api = APIClient()
    token = Token.objects.create(user=user)

    api.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    setattr(api, "user", user)
    return api


@pytest.fixture()
def monaiot_logged_in_user(db):
    """A Django test client logged in as a  mon aiot oidc user."""

    user = UserFactory(oidc_connexion=OIDCTypeChoice.MONAIOT)

    client = Client()
    client.force_login(user=user, backend="oidc.backends.MonAiotOidcBackend")

    session = client.session

    session["_auth_user_backend"] = settings.MONAIOT_BACKEND

    session.save()

    setattr(client, "user", user)
    return client


@pytest.fixture()
def proconnect_logged_in_user(db):
    """A Django test client logged in as a ."""

    user = UserFactory(oidc_connexion=OIDCTypeChoice.PROCONNECT)

    client = Client()
    client.force_login(user=user, backend="oidc.backends.ProconnectOidcBackend")

    session = client.session

    session["_auth_user_backend"] = settings.PROCONNECT_BACKEND

    session.save()

    setattr(client, "user", user)
    return client


@pytest.fixture()
def get_client(
    monaiot_logged_in_user,
    proconnect_logged_in_user,
    verified_user,
    request,
):
    """This fixture allows to easily run test with multiple clients.

    Just decorate your test with
    `@pytest.mark.parametrize('get_client', ['verified_client', 'logged_monaiot_user'], indirect=True)`
    """
    clients = {
        "verified_client": verified_user,
        "logged_monaiot_client": monaiot_logged_in_user,
        "logged_proconnect_client": proconnect_logged_in_user,
    }
    return clients.get(request.param)


@pytest.fixture()
def get_profile(
    verified_icpe,
    verified_ctt,
    verified_inspection_travail,
    verified_gendarme,
    verified_ars,
    verified_douane,
    verified_observatoire,
    verified_adm_centrale,
    request,
):
    """This fixture allows to easily run test with different user profiles.

    Just decorate your test with
    `@pytest.mark.parametrize('get_client', ['get_profile', 'verified_gendarme', 'verified_adm_centrale'], indirect=True)`
    """
    clients = {
        "verified_icpe": verified_icpe,
        "verified_ctt": verified_ctt,
        "verified_inspection_travail": verified_inspection_travail,
        "verified_gendarme": verified_gendarme,
        "verified_ars": verified_ars,
        "verified_douane": verified_douane,
        "verified_observatoire": verified_observatoire,
        "verified_adm_centrale": verified_adm_centrale,
    }

    ret = clients.get(request.param)

    return ret


@pytest.fixture()
def api_anon():
    """Return a DRF api client."""
    api = APIClient()
    return api


@pytest.fixture()
def logged_in_api():
    """Return a DRF api client with an already logged in (not verified)  user."""

    user = UserFactory()

    api = APIClient()
    api.login(email=user.email, password=DEFAULT_PASSWORD)

    setattr(api, "user", user)
    return api


@pytest.fixture()
def verified_api(logged_in_api):
    """Return a DRF api client with an already verified user."""

    client = logged_in_api

    device = EmailDeviceFactory(user=client.user)
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()

    return client


@pytest.fixture(scope="session", autouse=True)
def cleanup_s3_after_tests():
    """Clean up only files created during this test session."""
    test_start_time = dt.datetime.now(dt.timezone.utc)

    yield  # Run all tests

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    bucket = settings.AWS_S3_BUCKET_NAME  # Also: use AWS_STORAGE_BUCKET_NAME for django-storages

    paginator = s3.get_paginator("list_objects_v2")
    objects_to_delete = []

    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            if obj["LastModified"] >= test_start_time:
                objects_to_delete.append({"Key": obj["Key"]})

    if objects_to_delete:
        for i in range(0, len(objects_to_delete), 1000):
            batch = objects_to_delete[i : i + 1000]
            s3.delete_objects(Bucket=bucket, Delete={"Objects": batch})


class HTMXClient:
    def __init__(self, client):
        self._client = client

    def get(self, *args, **kwargs):
        kwargs.setdefault("HTTP_HX_REQUEST", "true")
        return self._client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        kwargs.setdefault("HTTP_HX_REQUEST", "true")
        return self._client.post(*args, **kwargs)

    def put(self, *args, **kwargs):
        kwargs.setdefault("HTTP_HX_REQUEST", "true")
        return self._client.put(*args, **kwargs)

    def patch(self, *args, **kwargs):
        kwargs.setdefault("HTTP_HX_REQUEST", "true")
        return self._client.patch(*args, **kwargs)

    def delete(self, *args, **kwargs):
        kwargs.setdefault("HTTP_HX_REQUEST", "true")
        return self._client.delete(*args, **kwargs)


@pytest.fixture
def htmx_client():
    """Factory that wraps any client with HTMX headers."""
    return lambda client: HTMXClient(client)
