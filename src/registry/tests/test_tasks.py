import datetime as dt
from unittest.mock import patch

import pytest
from celery.exceptions import Retry

from registry.constants import RegistryV2DeclarationType, RegistryV2ExportState, RegistryV2WasteCode
from registry.task import refresh_registry_export

from ..factories import RegistryV2ExportSiretFactory
from ..task import generate_registry_export

pytestmark = pytest.mark.django_db


def test_generate_registry_export_success():
    registry_export = RegistryV2ExportSiretFactory()
    mock_response = {
        "data": {
            "generateRegistryV2Export": {
                "id": "mock-export-id-123",
                "status": RegistryV2ExportState.STARTED,
            }
        }
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response

        generate_registry_export(registry_export.pk)

        registry_export.refresh_from_db()

        assert registry_export.registry_export_id == "mock-export-id-123"
        assert registry_export.state == RegistryV2ExportState.STARTED

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs

        assert call_kwargs["url"] == "https://testapi.test"
        assert call_kwargs["headers"]["Authorization"] == "Bearer thetoken"

        request_payload = call_kwargs["json"]
        variables = request_payload["variables"]
        assert variables["siret"] == registry_export.siret
        assert variables["registryType"] == registry_export.parent.registry_type
        assert variables["format"] == registry_export.parent.export_format


def test_generate_registry_export_with_advanced_params_success():
    registry_export = RegistryV2ExportSiretFactory(
        parent__start_date=dt.datetime.fromisoformat("2024-12-31T23:00:00+00:00"),
        parent__end_date=dt.datetime.fromisoformat("2025-12-31T23:00:00+00:00"),
        parent__declaration_type=RegistryV2DeclarationType.BSD,
        parent__waste_types_dnd=True,
        parent__waste_types_dd=True,
        parent__waste_types_texs=True,
        parent__waste_codes=[RegistryV2WasteCode.WASTE_01_01_01],
    )
    mock_response = {
        "data": {
            "generateRegistryV2Export": {
                "id": "mock-export-id-123",
                "status": RegistryV2ExportState.STARTED,
            }
        }
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response

        generate_registry_export(registry_export.pk)

        registry_export.refresh_from_db()

        assert registry_export.registry_export_id == "mock-export-id-123"
        assert registry_export.state == RegistryV2ExportState.STARTED

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs

        assert call_kwargs["url"] == "https://testapi.test"
        assert call_kwargs["headers"]["Authorization"] == "Bearer thetoken"

        request_payload = call_kwargs["json"]
        variables = request_payload["variables"]

        assert variables == {
            "siret": registry_export.siret,
            "registryType": "INCOMING",
            "format": "CSV",
            "dateRange": {"_gte": "2024-12-31T23:00:00+00:00", "_lte": "2025-12-31T23:00:00+00:00"},
            "where": {
                "declarationType": {"_eq": "BSD"},
                "wasteType": {"_in": ["DND", "DD", "TEXS"]},
                "wasteCode": {"_in": ["01 01 01"]},
            },
        }


def test_generate_registry_export_api_error():
    registry_export = RegistryV2ExportSiretFactory()

    mock_error_response = {"errors": [{"message": "Export generation failed"}]}

    # Mock the task class with the retry method
    with patch("celery.app.task.Task.retry", side_effect=Retry()) as mock_retry:
        with patch("httpx.Client.post") as mock_post:
            mock_post.return_value.json.return_value = mock_error_response

            with pytest.raises(Retry):
                generate_registry_export(registry_v2_export_pk=registry_export.pk)

            mock_post.assert_called_once()

            mock_retry.assert_called_once()

            registry_export.refresh_from_db()

            assert registry_export.registry_export_id == ""
            assert registry_export.state == RegistryV2ExportState.PENDING


def test_generate_registry_export_request_exception():
    registry_export = RegistryV2ExportSiretFactory()
    with patch("httpx.Client.post") as mock_post:
        mock_post.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            generate_registry_export(registry_export.pk)

        registry_export.refresh_from_db()

        assert registry_export.registry_export_id == ""
        assert registry_export.state == RegistryV2ExportState.PENDING


def test_refresh_registry_export_success():
    registry_export = RegistryV2ExportSiretFactory(registry_export_id="wxcvbn")

    mock_response = {
        "data": {
            "registryV2Export": {
                "id": "wxcvbn",
                "status": RegistryV2ExportState.SUCCESSFUL,
            }
        }
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        with patch("celery.app.task.Task.retry"):
            refresh_registry_export(registry_export.pk)

        registry_export.refresh_from_db()
        assert registry_export.state == RegistryV2ExportState.SUCCESSFUL

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs

        assert call_kwargs["url"] == "https://testapi.test"
        assert call_kwargs["headers"]["Authorization"] == "Bearer thetoken"

        request_payload = call_kwargs["json"]
        assert "query" in request_payload
        assert request_payload["variables"]["id"] == registry_export.registry_export_id


def test_refresh_registry_export_in_progress():
    registry_export = RegistryV2ExportSiretFactory(registry_export_id="wxcvbn")

    mock_response = {
        "data": {
            "registryV2Export": {
                "id": "wxcvbn",  # Match the ID with the factory
                "status": RegistryV2ExportState.STARTED,
            }
        }
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        with patch("celery.app.task.Task.retry", side_effect=Retry()) as mock_retry:
            with pytest.raises(Retry):
                refresh_registry_export(registry_v2_export_pk=registry_export.pk)

            mock_retry.assert_called_once()

            mock_post.assert_called_once()

            registry_export.refresh_from_db()

            assert registry_export.state == RegistryV2ExportState.PENDING  # Adjust based on your factory default


def test_refresh_registry_export_failed():
    registry_export = RegistryV2ExportSiretFactory(registry_export_id="wxcvbn")

    mock_response = {
        "data": {
            "registryV2Export": {
                "id": "wxcvbn",  # Match the ID with the factory
                "status": RegistryV2ExportState.FAILED,
            }
        }
    }

    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        with patch("celery.app.task.Task.retry"):
            refresh_registry_export(registry_v2_export_pk=registry_export.pk)

        registry_export.refresh_from_db()
        assert registry_export.state == RegistryV2ExportState.FAILED

        # Verify API was called correctly
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs

        # Verify URL and auth token
        assert call_kwargs["url"] == "https://testapi.test"
        assert call_kwargs["headers"]["Authorization"] == "Bearer thetoken"

        # Verify the request payload
        request_payload = call_kwargs["json"]
        assert "query" in request_payload
        assert request_payload["variables"]["id"] == registry_export.registry_export_id


def test_refresh_registry_export_request_exception():
    registry_export = RegistryV2ExportSiretFactory(registry_export_id="wxcvbn")

    with patch("httpx.Client.post") as mock_post:
        mock_post.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            refresh_registry_export(registry_export.pk)

        registry_export.refresh_from_db()

        assert registry_export.state == RegistryV2ExportState.PENDING
