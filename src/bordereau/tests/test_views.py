from unittest.mock import patch
import json

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from bordereau.factories import BsdPdfFactory, PdfBundleFactory
from bordereau.models import BsdPdf, PdfBundle

pytestmark = pytest.mark.django_db


def test_bsd_search_anon(anon_client):
    url = reverse("bordereau_search")
    res = anon_client.get(url)
    assert res.status_code == 302


@pytest.mark.parametrize(
    "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
)
def test_bsd_search(get_client):
    res = get_client.get(reverse("bordereau_search"))
    assert res.status_code == 200
    assert "Bordereaux" in res.content.decode()


def test_bsd_simple_search_view(verified_user):
    res = verified_user.get(reverse("bordereau_simple_search"))
    assert res.status_code == 200
    assert "Recherche simple" in res.content.decode()
    assert "<form" in res.content.decode()
    assert "id_search_clue" in res.content.decode()


def test_bsd_advanced_search_view(verified_user):
    res = verified_user.get(reverse("bordereau_advanced_search"))
    assert res.status_code == 200
    assert "Recherche avancée" in res.content.decode()
    assert "id_code_dechet" in res.content.decode()


def test_bordereau_recent_search_anon(anon_client):
    res = anon_client.get(reverse("bordereau_recent_search"))
    assert res.status_code == 302


def test_bordereau_recent_search(verified_user):
    other_user = UserFactory()
    BsdPdfFactory(created_by=other_user)
    BsdPdfFactory(created_by=verified_user.user, bsd_id="BSD-RECENT-1")
    PdfBundleFactory(created_by=other_user, state=PdfBundle.BundleChoice.READY)
    PdfBundleFactory(created_by=verified_user.user, state=PdfBundle.BundleChoice.PROCESSING)

    res = verified_user.get(reverse("bordereau_recent_search"))
    assert res.status_code == 200
    assert "BSD-RECENT-1" in res.content.decode()


def test_bsd_search_result_form_selection(verified_user):
    res_simple = verified_user.post(reverse("bordereau_search_result"), data={"bsd_id": "BSD-123"})
    assert res_simple.status_code == 200

    res_adv = verified_user.post(reverse("bordereau_search_result"), data={"code_dechet": "01 01 01"})
    assert res_adv.status_code == 200

@patch("bordereau.views.query_td_search_companies")
def test_company_search_view_with_clue(mock_search, verified_user):
    mock_search.return_value = [
        {"siret": "12345678901234", "name": "TEST COMPANY", "address": "PARIS"}
    ]
    res = verified_user.get(reverse("bordereau_company_search"), {"search_clue": "test", "code_postal": ""})
    assert res.status_code == 200
    assert "TEST COMPANY" in res.content.decode()

@patch("bordereau.views.query_td_search_companies")
def test_company_search_view_persistence_json(mock_search, verified_user):
    company_data = {"siret": "99999999999999", "name": "CACHED COMPANY", "address": "LYON"}
    res = verified_user.get(
        reverse("bordereau_company_search"),
        {"search_clue": "", "code_postal": "", "selected_siret": "99999999999999", "selected_company_json": json.dumps(company_data)},
    )
    assert res.status_code == 200
    assert "CACHED COMPANY" in res.content.decode()
    mock_search.assert_not_called()