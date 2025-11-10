import pytest
from django.urls import reverse

from accounts.constants import UserCategoryChoice

pytestmark = pytest.mark.django_db


def test_map_view_deny_anon(anon_client):
    url = reverse("map_view")
    res = anon_client.get(url)
    assert res.status_code == 302


def test_map_view_deny_non_verified_user(logged_in_user):
    url = reverse("map_view")
    res = logged_in_user.get(url)
    assert res.status_code == 302
    assert res.url == reverse("second_factor")


@pytest.mark.parametrize(
    "category",
    [
        UserCategoryChoice.STAFF_TD,
        UserCategoryChoice.ADMINISTRATION_CENTRALE,
        UserCategoryChoice.INSPECTEUR_ICPE,
        UserCategoryChoice.CTT,
        UserCategoryChoice.INSPECTION_TRAVAIL,
        UserCategoryChoice.GENDARMERIE,
        UserCategoryChoice.ARS,
        UserCategoryChoice.DOUANE,
        UserCategoryChoice.OBSERVATOIRE,
    ],
)
def test_map_view(verified_user, category):
    user = verified_user.user
    user.user_category = category
    user.save()
    url = reverse("map_view")
    res = verified_user.get(url)
    assert res.status_code == 200


def test_icpe_map_view_deny_anon(anon_client):
    url = reverse("icpe_map_view")
    res = anon_client.get(url)
    assert res.status_code == 302


@pytest.mark.parametrize(
    "category",
    [
        UserCategoryChoice.OBSERVATOIRE,
        UserCategoryChoice.CTT,
        UserCategoryChoice.INSPECTION_TRAVAIL,
        UserCategoryChoice.ARS,
        UserCategoryChoice.DOUANE,
    ],
)
def test_icpe_map_view_deny_user(verified_user, category):
    user = verified_user.user
    user.user_category = category
    user.save()

    url = reverse("icpe_map_view")
    res = verified_user.get(url)
    assert res.status_code == 403


@pytest.mark.parametrize(
    "category",
    [
        UserCategoryChoice.STAFF_TD,
        UserCategoryChoice.ADMINISTRATION_CENTRALE,
        UserCategoryChoice.INSPECTEUR_ICPE,
        UserCategoryChoice.GENDARMERIE,
    ],
)
def test_icpe_map_view(verified_user, category):
    user = verified_user.user
    user.user_category = category
    user.save()

    url = reverse("icpe_map_view")
    res = verified_user.get(url)
    assert res.status_code == 200
