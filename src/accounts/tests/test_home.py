import pytest
from django.urls import reverse

from accounts.models import UserCategoryChoice
from common.models import SiteConfiguration
from faq.factories import WebinarFactory

pytestmark = pytest.mark.django_db


def test_public_home(anon_client):
    config = SiteConfiguration.get_solo()

    url = reverse("public_home")
    res = anon_client.get(url)

    assert "lorem ipsum" not in res.content.decode()

    config.banner_content = "lorem ipsum"
    config.welcome_content = "welcome content"
    config.save()
    res = anon_client.get(url)
    assert "lorem ipsum" in res.content.decode()
    assert "welcome content" in res.content.decode()


def test_home(verified_user):
    config = SiteConfiguration.get_solo()
    config.welcome_content_connected = "welcome content connected"
    config.save()

    webinar = WebinarFactory(future=True)
    url = reverse("private_home")
    res = verified_user.get(url)
    assert res.status_code == 200

    assert "Admin équipe" not in res.content.decode()

    assert webinar.title in res.content.decode()
    assert "welcome content connected" in res.content.decode()


def test_home_administration_centrale_menu(verified_adm_centrale):
    url = reverse("private_home")
    res = verified_adm_centrale.get(url)
    assert res.status_code == 200

    assert "Fiche établissement" in res.content.decode()
    assert "Registre établissement" in res.content.decode()
    assert "Bordereau" in res.content.decode()
    assert "Cartographie" in res.content.decode()
    assert "Admin équipe" not in res.content.decode()
    assert "Observatoires" in res.content.decode()
    assert "Aide" in res.content.decode()


def test_home_observatoire_menu(verified_observatoire):
    url = reverse("private_home")
    res = verified_observatoire.get(url)
    assert res.status_code == 200

    assert "Fiche établissement" not in res.content.decode()
    assert "Registre établissement" not in res.content.decode()
    assert "Bordereau" not in res.content.decode()
    assert "Cartographie" in res.content.decode()
    assert "Admin équipe" not in res.content.decode()
    assert "Observatoires" in res.content.decode()
    assert "Aide" in res.content.decode()


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
def test_home_menu(get_profile):
    url = reverse("private_home")
    res = get_profile.get(url)
    assert res.status_code == 200

    assert "Fiche établissement" in res.content.decode()
    assert "Registre établissement" in res.content.decode()
    assert "Bordereau" in res.content.decode()
    assert "Cartographie" in res.content.decode()
    assert "Admin équipe" not in res.content.decode()
    assert "Observatoires" not in res.content.decode()
    assert "Aide" in res.content.decode()


@pytest.mark.parametrize(
    "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
)
def test_private_home_menu(get_client):
    url = reverse("private_home")
    res = get_client.get(url)
    assert res.status_code == 200

    assert "Établissements" in res.content.decode()
    assert "Fiche établissement" in res.content.decode()
    assert "Registre établissement" in res.content.decode()
    assert "Contrôle routier" in res.content.decode()
    assert "Bordereau" in res.content.decode()

    assert "Admin équipe" not in res.content.decode()
    assert "Observatoires" not in res.content.decode()
    assert "Cartographie" in res.content.decode()

    assert "Aide" in res.content.decode()


@pytest.mark.parametrize(
    "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
)
def test_private_home_menu_for_administration_central(get_client):
    user = get_client.user
    user.user_category = UserCategoryChoice.ADMINISTRATION_CENTRALE
    user.save()

    user.refresh_from_db()

    url = reverse("private_home")
    res = get_client.get(url)
    assert res.status_code == 200
    assert "Fiche établissement" in res.content.decode()
    assert "Registre établissement" in res.content.decode()

    assert "Bordereau" in res.content.decode()

    assert "Admin équipe" not in res.content.decode()
    assert "Observatoires" in res.content.decode()
    assert "Contrôle routier" in res.content.decode()
    assert "Cartographie" in res.content.decode()
    assert "Bordereau" in res.content.decode()

    assert "Aide" in res.content.decode()


@pytest.mark.parametrize(
    "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
)
def test_private_home_menu_for_icpe(get_client):
    user = get_client.user
    user.user_category = UserCategoryChoice.INSPECTEUR_ICPE
    user.save()

    user.refresh_from_db()

    url = reverse("private_home")
    res = get_client.get(url)
    assert res.status_code == 200
    assert "Fiche établissement" in res.content.decode()
    assert "Registre établissement" in res.content.decode()
    assert "Bordereau" in res.content.decode()

    assert "Admin équipe" not in res.content.decode()
    assert "Observatoires" not in res.content.decode()
    assert "Contrôle routier" in res.content.decode()
    assert "Cartographie" in res.content.decode()
    assert "Bordereau" in res.content.decode()
    assert "Aide" in res.content.decode()


@pytest.mark.parametrize(
    "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
)
def test_private_home_menu_for_ctt(get_client):
    user = get_client.user
    user.user_category = UserCategoryChoice.CTT
    user.save()

    user.refresh_from_db()

    url = reverse("private_home")
    res = get_client.get(url)
    assert res.status_code == 200
    assert "Fiche établissement" in res.content.decode()
    assert "Registre établissement" in res.content.decode()
    assert "Bordereau" in res.content.decode()

    assert "Admin équipe" not in res.content.decode()
    assert "Observatoires" not in res.content.decode()
    assert "Contrôle routier" in res.content.decode()
    assert "Cartographie" in res.content.decode()
    assert "Bordereau" in res.content.decode()
    assert "Aide" in res.content.decode()

    @pytest.mark.parametrize(
        "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
    )
    def test_private_home_menu_for_inspection_travail(get_client):
        user = get_client.user
        user.user_category = UserCategoryChoice.INSPECTION_TRAVAIL
        user.save()

        user.refresh_from_db()

        url = reverse("private_home")
        res = get_client.get(url)
        assert res.status_code == 200
        assert "Fiche établissement" in res.content.decode()
        assert "Registre établissement" in res.content.decode()
        assert "Bordereau" in res.content.decode()

        assert "Admin équipe" not in res.content.decode()
        assert "Observatoires" not in res.content.decode()
        assert "Contrôle routier" not in res.content.decode()
        assert "Cartographie" in res.content.decode()
        assert "Bordereau" in res.content.decode()
        assert "Aide" in res.content.decode()

    @pytest.mark.parametrize(
        "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
    )
    def test_private_home_menu_for_poulets(get_client):
        user = get_client.user
        user.user_category = UserCategoryChoice.GENDARMERIE
        user.save()

        user.refresh_from_db()

        url = reverse("private_home")
        res = get_client.get(url)
        assert res.status_code == 200
        assert "Fiche établissement" in res.content.decode()
        assert "Registre établissement" in res.content.decode()
        assert "Bordereau" in res.content.decode()

        assert "Admin équipe" not in res.content.decode()
        assert "Observatoires" not in res.content.decode()
        assert "Contrôle routier" not in res.content.decode()
        assert "Cartographie" in res.content.decode()
        assert "Bordereau" in res.content.decode()
        assert "Aide" in res.content.decode()

    @pytest.mark.parametrize(
        "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
    )
    def test_private_home_menu_for_douane(get_client):
        user = get_client.user
        user.user_category = UserCategoryChoice.DOUANE
        user.save()

        user.refresh_from_db()

        url = reverse("private_home")
        res = get_client.get(url)
        assert res.status_code == 200
        assert "Fiche établissement" in res.content.decode()
        assert "Registre établissement" in res.content.decode()
        assert "Bordereau" in res.content.decode()

        assert "Admin équipe" not in res.content.decode()
        assert "Observatoires" not in res.content.decode()
        assert "Contrôle routier" not in res.content.decode()
        assert "Cartographie" in res.content.decode()
        assert "Bordereau" in res.content.decode()
        assert "Aide" in res.content.decode()


@pytest.mark.parametrize(
    "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
)
def test_private_home_menu_for_observatoire(get_client):
    user = get_client.user
    user.user_category = UserCategoryChoice.OBSERVATOIRE
    user.save()

    user.refresh_from_db()

    assert user.is_observatoire

    url = reverse("private_home")
    res = get_client.get(url)
    assert res.status_code == 200
    assert "Fiche établissement" not in res.content.decode()
    assert "Registre établissement" not in res.content.decode()
    assert "Bordereau" not in res.content.decode()

    assert "Admin équipe" not in res.content.decode()
    assert "Observatoires" in res.content.decode()
    assert "Contrôle routier" not in res.content.decode()
    assert "Cartographie" in res.content.decode()
    assert "Bordereau" not in res.content.decode()
    assert "Aide" in res.content.decode()


def test_home_for_staff(verified_staff):
    url = reverse("private_home")
    res = verified_staff.get(url)
    assert res.status_code == 200
    assert res.status_code == 200
    assert "Fiche établissement" in res.content.decode()
    assert "Registre établissement" in res.content.decode()

    assert "Bordereau" in res.content.decode()

    assert "Observatoires" in res.content.decode()
    assert "Contrôle routier" in res.content.decode()
    assert "Cartographie" in res.content.decode()
    assert "Admin équipe" in res.content.decode()
    assert "Aide" in res.content.decode()
