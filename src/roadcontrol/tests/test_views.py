from unittest.mock import patch

import pytest
from django.urls import reverse

from accounts.factories import UserFactory

from ..factories import BsdPdfFactory, PdfBundleFactory
from ..models import PdfBundle

pytestmark = pytest.mark.django_db

import json

# Road control search


def test_roadcontrol_anon(anon_client):
    url = reverse("roadcontrol")
    res = anon_client.get(url)
    assert res.status_code == 302


def test_roadcontrol_observatoires(verified_observatoire):
    url = reverse("roadcontrol")
    res = verified_observatoire.get(url)
    assert res.status_code == 403


@pytest.mark.parametrize(
    "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
)
def test_roadcontrol(get_client):
    url = reverse("roadcontrol")
    res = get_client.get(url)
    assert res.status_code == 200

    assert "Rechercher un transport" in res.content.decode()


def test_roadcontrol_pdf_bundle_anon(anon_client):
    url = reverse("roadcontrol_pdf_bundle")
    res = anon_client.get(url)
    assert res.status_code == 302


def test_roadcontrol_pdf_observatoires(verified_observatoire):
    url = reverse("roadcontrol_pdf_bundle")
    res = verified_observatoire.get(url)
    assert res.status_code == 403


def test_roadcontrol_pdf_bundle(verified_user):
    url = reverse("roadcontrol_pdf_bundle")
    res = verified_user.get(url)
    assert res.status_code == 200


def test_roadcontrol_recent_pdfs_anon(anon_client):
    url = reverse("roadcontrol_recent_pdfs")
    res = anon_client.get(url)
    assert res.status_code == 302


def test_roadcontrol_recent_pdfs_observatoires(verified_observatoire):
    url = reverse("roadcontrol_pdf_bundle")
    res = verified_observatoire.get(url)
    assert res.status_code == 403


def test_roadcontrol_recent_pdfs(verified_user):
    other_user = UserFactory()
    other_bsd = BsdPdfFactory(created_by=other_user)
    other_bundle = PdfBundleFactory(created_by=other_user, state=PdfBundle.BundleChoice.READY)

    bsd = BsdPdfFactory(created_by=verified_user.user)
    bundle = PdfBundleFactory(created_by=verified_user.user, state=PdfBundle.BundleChoice.READY)
    non_ready_bundle = PdfBundleFactory(created_by=verified_user.user, state=PdfBundle.BundleChoice.PROCESSING)
    url = reverse("roadcontrol_recent_pdfs")
    res = verified_user.get(url)

    assert res.status_code == 200

    assert str(bsd.id) in res.content.decode()
    assert str(bundle.id) in res.content.decode()

    assert str(other_bsd.id) not in res.content.decode()
    assert str(other_bundle.id) not in res.content.decode()
    assert str(non_ready_bundle.id) not in res.content.decode()


def test_roadcontrol_pdf_bundle_result_anon(anon_client):
    bundle = PdfBundleFactory(state=PdfBundle.BundleChoice.READY)
    url = reverse("roadcontrol_pdf_bundle_result", args=[bundle.pk])
    res = anon_client.get(url)
    assert res.status_code == 302


def test_roadcontrol_pdf_bundle_result(verified_user):
    bundle = PdfBundleFactory(created_by=verified_user.user, state=PdfBundle.BundleChoice.READY)

    url = reverse("roadcontrol_pdf_bundle_result", args=[bundle.pk])
    res = verified_user.get(url)
    assert res.status_code == 200

    other_user = UserFactory()
    other_bundle = PdfBundleFactory(created_by=other_user, state=PdfBundle.BundleChoice.READY)

    url = reverse("roadcontrol_pdf_bundle_result", args=[other_bundle.pk])
    res = verified_user.get(url)
    assert res.status_code == 404

def test_single_bsd_pdf_download_anon(anon_client):
    url = reverse("single_bsd_pdf_download")
    res = anon_client.get(url)
    assert res.status_code == 302


@pytest.mark.parametrize(
    "get_profile",
    [
        "verified_icpe",
        "verified_ctt",
        "verified_inspection_travail",
        "verified_gendarme",
        "verified_ars",
        "verified_douane",
        "verified_adm_centrale",
    ],
    indirect=True,
)
def test_single_bsd_pdf_download_is_allowed(get_profile):
    url = reverse("single_bsd_pdf_download")
    res = get_profile.get(url)
    assert res.status_code == 200


@pytest.mark.parametrize(
    "get_profile",
    ["verified_observatoire"],
    indirect=True,
)
def test_single_bsd_pdf_download_is_denied(get_profile):
    url = reverse("single_bsd_pdf_download")
    res = get_profile.get(url)
    assert res.status_code == 403


def test_roadcontrol_search_result_anon(anon_client):
    url = reverse("roadcontrol_search_result")
    res = anon_client.get(url)
    assert res.status_code == 302


def test_roadcontrol_search_result_observatoires(verified_observatoire):
    url = reverse("roadcontrol_search_result")
    res = verified_observatoire.get(url)
    assert res.status_code == 403


def test_roadcontrol_search_result(verified_user):
    url = reverse("roadcontrol_search_result")
    res = verified_user.get(url)
    assert res.status_code == 200


def mock_graphql_response_factory(has_next_page=True):
    return {
        "data": {
            "controlBsds": {
                "totalCount": 123,
                "pageInfo": {
                    "startCursor": "id_1",
                    "endCursor": "id_3",
                    "hasNextPage": has_next_page,
                    "hasPreviousPage": False,
                },
                "edges": [
                    {
                        "node": {
                            "__typename": "Form",
                            "id": "id_1",
                            "readableId": "BSD-20220407-CWXDTABC",
                            "updatedAt": "2022-04-07T08:20:46.752Z",
                            "bsddStatus": "SENT",
                            "wasteDetails": {
                                "code": "15 02 02*",
                                "name": "FILTRE CABINE TRANSFERT SFG",
                                "onuCode": "UN 3088 DECHET Solide organique auto-échauffant, n.s.a. (filtres auto-echauffants), 4.2, III, (E)",
                                "quantity": 1.057,
                                "packagingInfos": [{"type": "GRV", "other": None, "quantity": 1}],
                            },
                            "stateSummary": {"quantity": 1.057},
                            "emitter": {"company": {"name": "THE COMPANY"}, "workSite": None},
                            "recipient": {"company": {"name": "THE COMPANY"}},
                            "transporters": [{"company": {"name": "THE COMPANY"}, "numberPlate": "AB-12-KL"}],
                            "transporter": {
                                "company": {"siret": "12345889300041", "name": "THE COMPANY"},
                                "numberPlate": "AB-12-KL",
                            },
                        }
                    },
                    {
                        "node": {
                            "__typename": "Form",
                            "id": "id_2",
                            "readableId": "BSD-20220407-WZZ449ABCY",
                            "updatedAt": "2022-04-07T08:20:46.874Z",
                            "bsddStatus": "SENT",
                            "wasteDetails": {
                                "code": "15 01 10*",
                                "name": "EMBALLAGES SOUILLES SPECIAUX 8 TRANSFERT SFG",
                                "onuCode": "UN 2923 DECHET Solide corrosif, toxique, n.s.a. (emballages souillés), 8(6.1), III, (E)",
                                "quantity": 0.149,
                                "packagingInfos": [{"type": "GRV", "other": None, "quantity": 1}],
                            },
                            "stateSummary": {"quantity": 0.149},
                            "emitter": {"company": {"name": "THE COMPANY"}, "workSite": None},
                            "recipient": {"company": {"name": "THE COMPANY"}},
                            "transporters": [{"company": {"name": "THE COMPANY"}, "numberPlate": "AB-12-KL"}],
                            "transporter": {
                                "company": {"siret": "12345889300041", "name": "THE COMPANY"},
                                "numberPlate": "AB-12-KL",
                            },
                        }
                    },
                    {
                        "node": {
                            "__typename": "Form",
                            "id": "id_3",
                            "readableId": "BSD-20220407-2ZD5GPABC",
                            "updatedAt": "2022-04-07T08:20:47.032Z",
                            "bsddStatus": "SENT",
                            "wasteDetails": {
                                "code": "15 01 10*",
                                "name": "EMBALLAGES SOUILLES SPECIAUX 5 TRANSFERT SFG",
                                "onuCode": "UN 1479 DECHET Solide comburant, n.s.a. (emballages souillés), 5.1, III, (E)",
                                "quantity": 0.065,
                                "packagingInfos": [{"type": "GRV", "other": None, "quantity": 1}],
                            },
                            "stateSummary": {"quantity": 0.065},
                            "emitter": {"company": {"name": "THE COMPANY"}, "workSite": None},
                            "recipient": {"company": {"name": "THE COMPANY"}},
                            "transporters": [{"company": {"name": "THE COMPANY"}, "numberPlate": "AB-12-KL"}],
                            "transporter": {
                                "company": {"siret": "12345889300041", "name": "THE COMPANY"},
                                "numberPlate": "AB-12-KL",
                            },
                        }
                    },
                ],
            }
        }
    }


@patch("roadcontrol.views.query_td_control_bsds")
def test_road_control_search_result_success(
    mock_query_td,
    verified_user,
):
    """Test successful POST request to RoadControlSearchResult view"""

    # Setup mocks
    # mock_query_td.return_value = mock_graphql_response
    mock_query_td.return_value = mock_graphql_response_factory(has_next_page=True)

    # Prepare form data
    form_data = {"siret": "12345889300041", "plate": "AB-123-CD"}

    # Make POST request
    url = reverse("roadcontrol_search_result")  # Replace with actual URL name
    response = verified_user.post(url, data=form_data)

    # Assertions
    assert response.status_code == 200
    assert "bsds" in response.context
    assert "bsds_ids" in response.context
    assert "total_count" in response.context

    # Check context data
    assert response.context["total_count"] == 123
    assert response.context["has_next_page"] is True
    assert response.context["has_previous_page"] is False
    assert response.context["start_cursor"] == "id_1"
    assert response.context["end_cursor"] == "id_3"
    assert len(response.context["bsds_ids"]) == 3

    bsds = response.context["bsds"]
    assert len(bsds) == 3
    assert bsds[0]["readable_id"] == "BSD-20220407-CWXDTABC"
    assert bsds[1]["readable_id"] == "BSD-20220407-WZZ449ABCY"
    assert bsds[2]["readable_id"] == "BSD-20220407-2ZD5GPABC"

    # Verify API was called with correct parameters
    mock_query_td.assert_called_once_with(siret="12345889300041", plate="AB 123 CD", end_cursor="")


@pytest.mark.django_db
@patch("roadcontrol.views.query_td_control_bsds")
def test_road_control_search_no_results(mock_query_td, verified_user):
    mock_query_td.return_value = {
        "data": {
            "controlBsds": {
                "totalCount": 0,
                "pageInfo": {"startCursor": None, "endCursor": None, "hasNextPage": False, "hasPreviousPage": False},
                "edges": [],
            }
        }
    }

    form_data = {"siret": "12345678901234", "plate": "XY-999-ZZ"}

    url = reverse("roadcontrol_search_result")
    response = verified_user.post(url, data=form_data)

    assert response.status_code == 200
    assert response.context["total_count"] == 0
    assert response.context["no_bsd_found_pdf_available"] is True