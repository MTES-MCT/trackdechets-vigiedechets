from datetime import date
from unittest.mock import patch

import polars as pl
import pytest
from pandera.errors import SchemaError

from maps.data.datasets import Computed, get_data_df


@pytest.fixture
def mock_icpe_installations_df():
    return pl.DataFrame(
        {
            "code_aiot": ["AIOT001", "AIOT002"],
            "raison_sociale": ["Company A", "Company B"],
            "siret": ["12345678901234", "98765432109876"],
            "rubrique": ["2760", "2771"],
            "quantite_autorisee": [1000.0, 2000.0],
            "unite": ["t/an", "t/an"],
            "latitude": [48.8566, 45.764],
            "longitude": [2.3522, 4.8357],
            "adresse1": ["1 rue de Paris", "2 avenue Lyon"],
            "adresse2": ["", "Bâtiment B"],
            "code_postal": ["75001", "69001"],
            "commune": ["Paris", "Lyon"],
        }
    )


@pytest.fixture
def mock_icpe_installations_waste_processed_df():
    return pl.DataFrame(
        {
            "code_aiot": ["AIOT001", "AIOT002"],
            "rubrique": ["2760", "2771"],
            "raison_sociale": ["Company A", "Company B"],
            "siret": ["12345678901234", "98765432109876"],
            "adresse1": ["1 rue de Paris", "2 avenue Lyon"],
            "adresse2": ["", "Bâtiment B"],
            "code_postal": ["75001", "69001"],
            "commune": ["Paris", "Lyon"],
            "latitude": [48.8566, 45.764],
            "longitude": [2.3522, 4.8357],
            "quantite_autorisee": [1000.0, 2000.0],
            "unite": ["t/an", "t/an"],
            "quantite_traitee": [500.0, 1500.0],
            "day_of_processing": [date(2024, 1, 15), date(2024, 1, 15)],
            "quantite_objectif": [800.0, 1800.0],
        }
    )


@pytest.fixture
def mock_icpe_departements_waste_processed_df():
    return pl.DataFrame(
        {
            "code_departement_insee": ["75", "69"],
            "nom_departement": ["Paris", "Rhône"],
            "code_region_insee": ["11", "84"],
            "rubrique": ["2760", "2771"],
            "day_of_processing": [date(2024, 1, 15), date(2024, 1, 15)],
            "nombre_installations": [10, 20],
            "quantite_traitee": [5000.0, 15000.0],
            "quantite_autorisee": [10000.0, 30000.0],
        }
    )


@pytest.fixture
def mock_icpe_regions_waste_processed_df():
    return pl.DataFrame(
        {
            "code_region_insee": ["11", "84"],
            "nom_region": ["Île-de-France", "Auvergne-Rhône-Alpes"],
            "rubrique": ["2760", "2771"],
            "day_of_processing": [date(2024, 1, 15), date(2024, 1, 15)],
            "nombre_installations": [50, 100],
            "quantite_traitee": [25000.0, 75000.0],
            "quantite_autorisee": [50000.0, 150000.0],
        }
    )


@pytest.fixture
def mock_icpe_france_waste_processed_df():
    return pl.DataFrame(
        {
            "rubrique": ["2760", "2771"],
            "day_of_processing": [date(2024, 1, 15), date(2024, 1, 15)],
            "nombre_installations": [500, 1000],
            "quantite_traitee": [250000.0, 750000.0],
            "quantite_autorisee": [500000.0, 1500000.0],
        }
    )


def test_get_data_df_returns_computed_dataclass(
    mock_icpe_installations_df,
    mock_icpe_installations_waste_processed_df,
    mock_icpe_departements_waste_processed_df,
    mock_icpe_regions_waste_processed_df,
    mock_icpe_france_waste_processed_df,
):
    """Test that get_data_df returns a Computed dataclass with all datasets."""
    with patch("maps.data.datasets.extract_dataset") as mock_extract:
        mock_extract.side_effect = [
            mock_icpe_installations_df,
            mock_icpe_installations_waste_processed_df,
            mock_icpe_departements_waste_processed_df,
            mock_icpe_regions_waste_processed_df,
            mock_icpe_france_waste_processed_df,
        ]

        result = get_data_df()

        assert isinstance(result, Computed)
        assert mock_extract.call_count == 5


def test_get_data_df_calls_extract_dataset_with_correct_arguments(
    mock_icpe_installations_df,
    mock_icpe_installations_waste_processed_df,
    mock_icpe_departements_waste_processed_df,
    mock_icpe_regions_waste_processed_df,
    mock_icpe_france_waste_processed_df,
):
    """Test that get_data_df calls extract_dataset with the correct SQL and schema overrides."""
    with patch("maps.data.datasets.extract_dataset") as mock_extract:
        mock_extract.side_effect = [
            mock_icpe_installations_df,
            mock_icpe_installations_waste_processed_df,
            mock_icpe_departements_waste_processed_df,
            mock_icpe_regions_waste_processed_df,
            mock_icpe_france_waste_processed_df,
        ]

        get_data_df()

        calls = mock_extract.call_args_list
        assert len(calls) == 5

        # Check that each call includes SQL string and schema overrides
        for call in calls:
            args = call[0]
            assert len(args) == 2
            assert isinstance(args[0], str)  # SQL query
            assert isinstance(args[1], dict)  # Schema overrides


def test_get_data_df_datasets_have_correct_columns(
    mock_icpe_installations_df,
    mock_icpe_installations_waste_processed_df,
    mock_icpe_departements_waste_processed_df,
    mock_icpe_regions_waste_processed_df,
    mock_icpe_france_waste_processed_df,
):
    """Test that returned datasets have the expected columns."""
    with patch("maps.data.datasets.extract_dataset") as mock_extract:
        mock_extract.side_effect = [
            mock_icpe_installations_df,
            mock_icpe_installations_waste_processed_df,
            mock_icpe_departements_waste_processed_df,
            mock_icpe_regions_waste_processed_df,
            mock_icpe_france_waste_processed_df,
        ]

        result = get_data_df()

        # Check icpe_installations_data columns
        expected_installations_cols = {
            "code_aiot",
            "raison_sociale",
            "siret",
            "rubrique",
            "quantite_autorisee",
            "unite",
            "latitude",
            "longitude",
            "adresse1",
            "adresse2",
            "code_postal",
            "commune",
        }
        assert set(result.icpe_installations_data.columns) == expected_installations_cols

        # Check icpe_installations_waste_processed_data columns
        expected_waste_processed_cols = {
            "code_aiot",
            "rubrique",
            "raison_sociale",
            "siret",
            "adresse1",
            "adresse2",
            "code_postal",
            "commune",
            "latitude",
            "longitude",
            "quantite_autorisee",
            "unite",
            "quantite_traitee",
            "day_of_processing",
            "quantite_objectif",
        }
        assert set(result.icpe_installations_waste_processed_data.columns) == expected_waste_processed_cols

        # Check icpe_departements_waste_processed_data columns
        expected_departements_cols = {
            "code_departement_insee",
            "nom_departement",
            "code_region_insee",
            "rubrique",
            "day_of_processing",
            "nombre_installations",
            "quantite_traitee",
            "quantite_autorisee",
        }
        assert set(result.icpe_departements_waste_processed_data.columns) == expected_departements_cols

        # Check icpe_regions_waste_processed_data columns
        expected_regions_cols = {
            "code_region_insee",
            "nom_region",
            "rubrique",
            "day_of_processing",
            "nombre_installations",
            "quantite_traitee",
            "quantite_autorisee",
        }
        assert set(result.icpe_regions_waste_processed_data.columns) == expected_regions_cols

        # Check icpe_france_waste_processed_data columns
        expected_france_cols = {
            "rubrique",
            "day_of_processing",
            "nombre_installations",
            "quantite_traitee",
            "quantite_autorisee",
        }
        assert set(result.icpe_france_waste_processed_data.columns) == expected_france_cols


def test_computed_dataclass_validates_schema():
    """Test that Computed dataclass validates schema on initialization."""
    # Create DataFrame with missing required column
    invalid_df = pl.DataFrame(
        {
            "code_aiot": ["AIOT001"],
            # Missing other required columns
        }
    )

    valid_installations_df = pl.DataFrame(
        {
            "code_aiot": ["AIOT001"],
            "raison_sociale": ["Company A"],
            "siret": ["12345678901234"],
            "rubrique": ["2760"],
            "quantite_autorisee": [1000.0],
            "unite": ["t/an"],
            "latitude": [48.8566],
            "longitude": [2.3522],
            "adresse1": ["1 rue de Paris"],
            "adresse2": [""],
            "code_postal": ["75001"],
            "commune": ["Paris"],
        }
    )

    valid_waste_processed_df = pl.DataFrame(
        {
            "code_aiot": ["AIOT001"],
            "rubrique": ["2760"],
            "raison_sociale": ["Company A"],
            "siret": ["12345678901234"],
            "adresse1": ["1 rue de Paris"],
            "adresse2": [""],
            "code_postal": ["75001"],
            "commune": ["Paris"],
            "latitude": [48.8566],
            "longitude": [2.3522],
            "quantite_autorisee": [1000.0],
            "unite": ["t/an"],
            "quantite_traitee": [500.0],
            "day_of_processing": [date(2024, 1, 15)],
            "quantite_objectif": [800.0],
        }
    )

    valid_departements_df = pl.DataFrame(
        {
            "code_departement_insee": ["75"],
            "nom_departement": ["Paris"],
            "code_region_insee": ["11"],
            "rubrique": ["2760"],
            "day_of_processing": [date(2024, 1, 15)],
            "nombre_installations": [10],
            "quantite_traitee": [5000.0],
            "quantite_autorisee": [10000.0],
        }
    )

    valid_regions_df = pl.DataFrame(
        {
            "code_region_insee": ["11"],
            "nom_region": ["Île-de-France"],
            "rubrique": ["2760"],
            "day_of_processing": [date(2024, 1, 15)],
            "nombre_installations": [50],
            "quantite_traitee": [25000.0],
            "quantite_autorisee": [50000.0],
        }
    )

    valid_france_df = pl.DataFrame(
        {
            "rubrique": ["2760"],
            "day_of_processing": [date(2024, 1, 15)],
            "nombre_installations": [500],
            "quantite_traitee": [250000.0],
            "quantite_autorisee": [500000.0],
        }
    )

    with pytest.raises(SchemaError):
        Computed(
            icpe_installations_data=invalid_df,
            icpe_installations_waste_processed_data=valid_waste_processed_df,
            icpe_departements_waste_processed_data=valid_departements_df,
            icpe_regions_waste_processed_data=valid_regions_df,
            icpe_france_waste_processed_data=valid_france_df,
        )

    # Valid dataframes should not raise
    computed = Computed(
        icpe_installations_data=valid_installations_df,
        icpe_installations_waste_processed_data=valid_waste_processed_df,
        icpe_departements_waste_processed_data=valid_departements_df,
        icpe_regions_waste_processed_data=valid_regions_df,
        icpe_france_waste_processed_data=valid_france_df,
    )
    assert computed is not None


def test_get_data_df_datasets_have_correct_row_count(
    mock_icpe_installations_df,
    mock_icpe_installations_waste_processed_df,
    mock_icpe_departements_waste_processed_df,
    mock_icpe_regions_waste_processed_df,
    mock_icpe_france_waste_processed_df,
):
    """Test that returned datasets preserve row count from extract_dataset."""
    with patch("maps.data.datasets.extract_dataset") as mock_extract:
        mock_extract.side_effect = [
            mock_icpe_installations_df,
            mock_icpe_installations_waste_processed_df,
            mock_icpe_departements_waste_processed_df,
            mock_icpe_regions_waste_processed_df,
            mock_icpe_france_waste_processed_df,
        ]

        result = get_data_df()

        assert len(result.icpe_installations_data) == 2
        assert len(result.icpe_installations_waste_processed_data) == 2
        assert len(result.icpe_departements_waste_processed_data) == 2
        assert len(result.icpe_regions_waste_processed_data) == 2
        assert len(result.icpe_france_waste_processed_data) == 2
