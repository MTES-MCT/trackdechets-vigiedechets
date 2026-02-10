import datetime as dt
from unittest.mock import patch

import pytest
from django.urls import reverse

from ..factories import RegistryV2ExportFactory
from ..models import RegistryV2Export

pytestmark = pytest.mark.django_db


def test_registry_v2_deny_anon(anon_client):
    url = reverse("registry_v2_prepare")
    res = anon_client.get(url)
    assert res.status_code == 302


def test_registry_v2_deny_observatoire(verified_observatoire):
    url = reverse("registry_v2_prepare")
    res = verified_observatoire.get(url)
    assert res.status_code == 403


@pytest.mark.parametrize(
    "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
)
def test_registry_v2_prepare_v2(get_client):
    url = reverse("registry_v2_prepare")
    res = get_client.get(url)
    assert res.status_code == 200
    form = res.context["form"]
    today = dt.date.today()
    assert form.initial == {
        "start_date": (today - dt.timedelta(days=365)).isoformat(),
        "end_date": today.isoformat(),
    }
    assert form.fields["siret"]
    assert form.fields["registry_type"]
    assert form.fields["export_format"]
    assert form.fields["declaration_type"]
    assert form.fields["waste_types_dnd"]
    assert form.fields["waste_types_dd"]
    assert form.fields["waste_types_texs"]
    assert form.fields["waste_codes"]
    assert form.fields["start_date"].widget.attrs == {"max": today.isoformat()}
    assert form.fields["end_date"].widget.attrs == {
        "max": dt.date(day=31, month=12, year=dt.date.today().year).isoformat()
    }
    content = res.content.decode()
    assert "id_siret" in content
    assert "id_registry_type" in content
    assert "id_export_format" in content
    assert "id_start_date" in content
    assert "id_end_date" in content


@pytest.mark.parametrize(
    "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
)
def test_registry_prepare_v2_post(get_client):
    url = reverse("registry_v2_prepare")
    with patch("registry.views.process_export"):
        res = get_client.post(
            url,
            data={
                "identifier_type": "SIRET",
                "siret": "51212357100030",
                "registry_type": "INCOMING",
                "export_format": "CSV",
                "declaration_type": "ALL",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "waste_types_dd": True,
                "waste_types_dnd": False,
                "waste_types_texs": False,
                "waste_codes": [],
            },
        )
    assert res.status_code == 302
    assert res.url == reverse("registry_v2_prepare")
    reg = RegistryV2Export.objects.first()
    assert reg.pk
    assert reg.siret == "51212357100030"
    assert reg.state == "PENDING"


def test_registry_v2_prepare_form_valid_calls_task(verified_user):
    """Test that form_valid method calls process_export with correct args."""

    with patch("registry.views.process_export") as mock_process:
        url = reverse("registry_v2_prepare")

        form_data = {
            "identifier_type": "SIRET",
            "siret": "12345678900000",
            "registry_type": "INCOMING",
            "declaration_type": "ALL",
            "waste_types_dnd": True,  # At least one waste type is required
            "waste_types_dd": False,
            "waste_types_texs": False,
            "export_format": "CSV",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }

        # Submit the form
        response = verified_user.post(url, data=form_data)

        # Check that the view redirected to success URL
        assert response.status_code == 302
        assert response.url == reverse("registry_v2_prepare")

        # Check that a new RegistryV2Export was created
        export = RegistryV2Export.objects.latest("created_at")
        assert export.siret == form_data["siret"]
        assert export.registry_type == form_data["registry_type"]
        assert export.state == "PENDING"

        # Assert that process_export was called with the correct argument
        mock_process.assert_called_once_with(export.pk)


def test_registry_v2_list_content_deny_anon(anon_client):
    url = reverse("registry_v2_list_content")
    res = anon_client.get(url)
    assert res.status_code == 302


def test_registry_v2_list_content_deny_observatoire(verified_observatoire):
    url = reverse("registry_v2_list_content")
    res = verified_observatoire.get(url)
    assert res.status_code == 403


@pytest.mark.parametrize(
    "get_client", ["verified_client", "logged_monaiot_client", "logged_proconnect_client"], indirect=True
)
def test_registry_v2_list_content(get_client):
    other_user_reg = RegistryV2ExportFactory(siret="1234567")  # other user export
    reg = RegistryV2ExportFactory(created_by=get_client.user, siret="987654")
    url = reverse("registry_v2_list_content")
    res = get_client.get(url)
    assert res.status_code == 200
    assert reg.siret in res.content.decode()
    assert other_user_reg.siret not in res.content.decode()


def test_registry_v2_retrieve_deny_anon(anon_client):
    reg = RegistryV2ExportFactory()
    url = reverse("registry_v2_retrieve", args=[reg.pk])
    res = anon_client.get(url)
    assert res.status_code == 302


def test_registry_v2_retrieve_deny_observatoire(verified_observatoire):
    reg = RegistryV2ExportFactory(created_by=verified_observatoire.user)
    url = reverse("registry_v2_retrieve", args=[reg.pk])
    res = verified_observatoire.get(url)
    assert res.status_code == 403


def test_registry_v2_retrieve_success(verified_user):
    """Test successful retrieval of signed URL."""

    registry_export = RegistryV2ExportFactory(created_by=verified_user.user)
    # Mock API response with a signed URL
    mock_response = {
        "data": {"registryV2ExportDownloadSignedUrl": {"signedUrl": "https://test-signed-url.example.com/download"}}
    }

    with patch("httpx.Client.post") as mock_post:
        # Configure the mock to return a predefined response
        mock_post.return_value.json.return_value = mock_response

        # Make the request
        url = reverse("registry_v2_retrieve", args=[registry_export.pk])
        response = verified_user.post(url)

        # Check redirect to the signed URL
        assert response.status_code == 302
        assert response.url == "https://test-signed-url.example.com/download"

        # Verify the request was made with correct parameters
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs

        # Check API endpoint and auth
        assert call_kwargs["url"] == "https://testapi.test"
        assert call_kwargs["headers"]["Authorization"] == "Bearer thetoken"

        # Verify request payload
        request_payload = call_kwargs["json"]
        variables = request_payload["variables"]
        assert variables["exportId"] == registry_export.registry_export_id


def test_registry_v2_retrieve_api_error(verified_user):
    """Test handling of API error response."""

    registry_export = RegistryV2ExportFactory(created_by=verified_user.user)
    # Mock API error response
    mock_response = {"errors": [{"message": "Error retrieving download URL"}]}

    with patch("httpx.Client.post") as mock_post:
        # Configure the mock to return an error response
        mock_post.return_value.json.return_value = mock_response

        # Make the request
        url = reverse("registry_v2_retrieve", args=[registry_export.pk])
        response = verified_user.post(url, follow=True)

        # Check redirect to main view
        assert response.status_code == 200
        assert response.redirect_chain[-1][0] == reverse("registry_v2_prepare")

        # Check error message was added
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "Erreur, le registre n'a pu être téléchargé" in str(messages[0])


def test_registry_v2_retrieve_missing_data(
    verified_user,
):
    """Test handling of missing data in API response."""
    # Mock response with missing data structure

    registry_export = RegistryV2ExportFactory(created_by=verified_user.user)
    mock_response = {
        "data": {}  # Empty data without the expected fields
    }

    with patch("httpx.Client.post") as mock_post:
        # Configure the mock to return a response with missing data
        mock_post.return_value.json.return_value = mock_response

        # Make the request
        url = reverse("registry_v2_retrieve", args=[registry_export.pk])
        response = verified_user.post(url, follow=True)

        # Check redirect to main view
        assert response.status_code == 200
        assert response.redirect_chain[-1][0] == reverse("registry_v2_prepare")

        # Check error message was added
        # Check error message was added
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert "Erreur, le registre n'a pu être téléchargé" in str(messages[0])

    def test_registry_v2_retrieve_request_exception(
        verified_user,
    ):
        """Test handling of HTTP request exceptions."""

        registry_export = RegistryV2ExportFactory(created_by=verified_user.user)
        with patch("httpx.Client.post") as mock_post:
            # Configure the mock to raise an exception
            mock_post.side_effect = Exception("Network error")

            # Make the request
            url = reverse("registry_v2_retrieve", args=[registry_export.pk])
            with pytest.raises(Exception):
                verified_user.post(url)
        registry_export.refresh_from_db()

        assert registry_export.state == "PENDING"
