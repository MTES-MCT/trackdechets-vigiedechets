import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db

login_url = reverse("login")
second_factor_url = reverse("second_factor")


def test_data_export_list_deny_anon(anon_client):
    url = reverse("data_export_list")
    res = anon_client.get(url)
    assert res.status_code == 302
    assert res.url == f"{reverse('login')}?next={url}"


@pytest.mark.parametrize(
    "get_profile",
    [
        "verified_adm_centrale",
        "verified_observatoire",
    ],
    indirect=True,
)
def test_data_export_list_is_allowed(get_profile):
    url = reverse("data_export_list")
    res = get_profile.get(url)
    assert res.status_code == 200


@pytest.mark.parametrize(
    "get_profile",
    [
        "verified_icpe",
        "verified_ctt",
        "verified_inspection_travail",
        "verified_gendarme",
        "verified_ars",
        "verified_douane",
    ],
    indirect=True,
)
def test_data_export_list_is_denied(get_profile):
    url = reverse("data_export_list")
    res = get_profile.get(url)
    assert res.status_code == 403


def test_data_export_list_is_allowed_for_douane_with_allowed_email(verified_douane):
    verified_douane.user.email = "allowed_for_data_export@mail.test"
    verified_douane.user.save()

    url = reverse("data_export_list")
    res = verified_douane.get(url)
    assert res.status_code == 200
