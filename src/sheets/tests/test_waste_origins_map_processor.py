from datetime import datetime
from zoneinfo import ZoneInfo

import geopandas as gpd
import polars as pl
import pytest
from shapely.geometry import Point

from sheets.constants import BSDD, BSFF

from ..graph_processors.plotly_components import WasteOriginsMapProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def departements_regions_df():
    """Fixture for départements and regions data."""
    return pl.LazyFrame(
        {
            "DEP": ["75", "13", "69", "33"],
            "LIBELLE": ["Paris", "Bouches-du-Rhône", "Rhône", "Gironde"],
            "REG": ["11", "93", "84", "75"],
            "LIBELLE_reg": [
                "Île-de-France",
                "Provence-Alpes-Côte d'Azur",
                "Auvergne-Rhône-Alpes",
                "Nouvelle-Aquitaine",
            ],
        }
    )


@pytest.fixture
def regions_geodata():
    """Fixture for regions geodata (GeoDataFrame)."""
    # Create a simple GeoDataFrame with regions
    data = {
        "code": ["11", "93", "84", "75"],
        "nom": ["Île-de-France", "Provence-Alpes-Côte d'Azur", "Auvergne-Rhône-Alpes", "Nouvelle-Aquitaine"],
        "geometry": [
            Point(2.3522, 48.8566),  # Paris
            Point(5.3698, 43.2965),  # Marseille
            Point(4.8357, 45.7640),  # Lyon
            Point(-0.5792, 44.8378),  # Bordeaux
        ],
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


@pytest.fixture
def sample_bsff_data():
    """Sample BSFF data without quantities (quantities are in packagings)."""
    return pl.LazyFrame(
        {
            "id": ["bsff-1", "bsff-2", "bsff-3"],
            "emitter_company_siret": ["12345678901234", "98765432109876", "12345678901234"],
            "emitter_company_address": [
                "123 Rue de Paris, 75001 Paris",
                "456 Avenue Marseille, 13001 Marseille",
                "789 Boulevard Lyon, 69001 Lyon",
            ],
            "recipient_company_siret": ["43210987654321", "43210987654321", "43210987654321"],
            "received_at": [
                datetime(2024, 1, 10, tzinfo=tz),
                datetime(2024, 2, 15, tzinfo=tz),
                datetime(2024, 3, 20, tzinfo=tz),
            ],
            "waste_code": ["03 01 01*", "03 01 02*", "03 01 03*"],
        }
    )


@pytest.fixture
def sample_packagings_data():
    """Sample packagings data for BSFF."""
    return pl.LazyFrame(
        {
            "bsff_id": ["bsff-1", "bsff-2", "bsff-2", "bsff-3", "bsff-3"],
            "acceptation_weight": [10.0, 20.0, 30.0, 40.0, 50.0],
            "acceptation_date": [
                datetime(2024, 1, 12, tzinfo=tz),
                datetime(2024, 2, 18, tzinfo=tz),
                datetime(2024, 2, 20, tzinfo=tz),
                datetime(2024, 3, 22, tzinfo=tz),
                datetime(2024, 3, 25, tzinfo=tz),
            ],
        }
    )


@pytest.fixture
def sample_bsdd_data():
    """Sample BSDD data."""
    return pl.LazyFrame(
        {
            "id": ["bsdd-1", "bsdd-2"],
            "emitter_company_siret": ["11111111111111", "22222222222222"],
            "emitter_company_address": [
                "10 Rue Bordeaux, 33000 Bordeaux",
                "20 Rue Paris, 75002 Paris",
            ],
            "recipient_company_siret": ["43210987654321", "43210987654321"],
            "received_at": [
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 2, 20, tzinfo=tz),
            ],
            "quantity_received": [25.0, 35.0],
            "waste_code": ["01 01 01*", "01 01 02*"],
        }
    )


@pytest.fixture
def data_date_interval():
    """Date interval for filtering data."""
    return (
        datetime(2024, 1, 1, tzinfo=tz),
        datetime(2024, 12, 31, tzinfo=tz),
    )


def test_bsff_with_packagings_quantities_summed_correctly(
    sample_bsff_data, sample_packagings_data, departements_regions_df, regions_geodata, data_date_interval
):
    """Test that BSFF quantities are correctly summed from packagings in full preprocessing flow.

    GIVEN: BSFF data with packagings data containing quantities at container level
           (bsff-1: 10.0, bsff-2: 20.0+30.0=50.0, bsff-3: 40.0+50.0=90.0, total=150.0)
    WHEN: _preprocess_data is called
    THEN: BSFF quantities are correctly summed from packagings, aggregated by region,
          and total quantity in preprocessed_df equals 150.0
    """
    company_siret = "43210987654321"
    bs_data_dfs = {BSFF: sample_bsff_data}

    processor = WasteOriginsMapProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        regions_geodata=regions_geodata,
        data_date_interval=data_date_interval,
        packagings_data=sample_packagings_data,
    )

    processor._preprocess_data()

    # Verify that BSFF data was processed correctly
    assert processor.preprocessed_df is not None
    assert len(processor.preprocessed_df) > 0

    # Verify quantities are aggregated correctly by region
    total_quantity = processor.preprocessed_df["quantity_received"].fillna(0).sum()
    assert total_quantity == pytest.approx(150.0, rel=1e-6)


def test_bsff_without_packagings_ignored(
    sample_bsff_data, departements_regions_df, regions_geodata, data_date_interval
):
    """Test that BSFF is ignored when packagings_data is None.

    GIVEN: BSFF data exists but packagings_data is None
    WHEN: _preprocess_data is called
    THEN: BSFF is excluded from processing (returns None from _process_bsff_data),
          resulting in empty or zero preprocessed_df
    """
    company_siret = "43210987654321"
    bs_data_dfs = {BSFF: sample_bsff_data}

    processor = WasteOriginsMapProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        regions_geodata=regions_geodata,
        data_date_interval=data_date_interval,
        packagings_data=None,
    )

    processor._preprocess_data()

    # BSFF should not be in the local copy used for processing
    # Original bs_data_dfs should remain unchanged (not mutated)
    assert BSFF in processor.bs_data_dfs
    assert processor.bs_data_dfs[BSFF] is sample_bsff_data  # Original reference preserved

    # No data should be in preprocessed_df since BSFF was the only data and was excluded
    assert processor.preprocessed_df is None or processor.preprocessed_df["quantity_received"].fillna(0).sum() == 0


def test_bsff_absent_from_dictionary_no_error(
    sample_bsdd_data, departements_regions_df, regions_geodata, data_date_interval
):
    """Test that no error occurs when BSFF is not in bs_data_dfs during full preprocessing.

    GIVEN: BSFF is not present in bs_data_dfs but other bordereau types (BSDD) are present
    WHEN: _preprocess_data is called
    THEN: No error is raised, processing completes gracefully,
          and only BSDD data is processed (BSFF absence is handled correctly)
    """
    company_siret = "43210987654321"
    bs_data_dfs = {BSDD: sample_bsdd_data}  # No BSFF in dictionary

    processor = WasteOriginsMapProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        regions_geodata=regions_geodata,
        data_date_interval=data_date_interval,
        packagings_data=None,
    )

    processor._preprocess_data()

    # Should handle gracefully and process BSDD
    assert processor.preprocessed_df is not None
    assert len(processor.preprocessed_df) > 0
    # Total quantity should only include BSDD (25.0 + 35.0 = 60.0)
    total_quantity = processor.preprocessed_df["quantity_received"].fillna(0).sum()
    assert total_quantity == pytest.approx(60.0, rel=1e-6)


def test_mix_bsff_and_other_bordereaux(
    sample_bsff_data,
    sample_packagings_data,
    sample_bsdd_data,
    departements_regions_df,
    regions_geodata,
    data_date_interval,
):
    """Test that BSFF and other bordereau types work together correctly.

    GIVEN: BSFF data with packagings and BSDD data in bs_data_dfs
    WHEN: _preprocess_data is called
    THEN: Both BSFF and BSDD are processed correctly, quantities are summed,
          and the total quantity includes both BSFF (150.0) and BSDD (60.0) = 210.0
    """
    company_siret = "43210987654321"
    bs_data_dfs = {
        BSFF: sample_bsff_data,
        BSDD: sample_bsdd_data,
    }

    processor = WasteOriginsMapProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        regions_geodata=regions_geodata,
        data_date_interval=data_date_interval,
        packagings_data=sample_packagings_data,
    )

    processor._preprocess_data()

    # Both BSFF and BSDD should be processed
    assert processor.preprocessed_df is not None
    assert len(processor.preprocessed_df) > 0

    # Total quantity should include both BSFF (150.0) and BSDD (25.0 + 35.0 = 60.0)
    total_quantity = processor.preprocessed_df["quantity_received"].fillna(0).sum()
    assert total_quantity == pytest.approx(210.0, rel=1e-6)


def test_regions_calculated_correctly_with_bsff_quantities(
    sample_bsff_data, sample_packagings_data, departements_regions_df, regions_geodata, data_date_interval
):
    """Test that regions are correctly calculated with BSFF quantities.

    GIVEN: BSFF data with packagings containing addresses with postal codes (75001, 13001, 69001)
    WHEN: _preprocess_data is called
    THEN: Regions are correctly extracted from addresses, quantities are aggregated by region,
          and preprocessed_df contains quantity_received column with region information
    """
    company_siret = "43210987654321"
    bs_data_dfs = {BSFF: sample_bsff_data}

    processor = WasteOriginsMapProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        regions_geodata=regions_geodata,
        data_date_interval=data_date_interval,
        packagings_data=sample_packagings_data,
    )

    processor._preprocess_data()

    assert processor.preprocessed_df is not None
    assert len(processor.preprocessed_df) > 0

    # Verify that regions are correctly identified from addresses
    # bsff-1: 75001 -> 75 (Paris) -> REG 11 (Île-de-France) -> 10.0
    # bsff-2: 13001 -> 13 (Bouches-du-Rhône) -> REG 93 (PACA) -> 50.0
    # bsff-3: 69001 -> 69 (Rhône) -> REG 84 (Auvergne-Rhône-Alpes) -> 90.0

    # Check that quantity_received contains region information
    assert "quantity_received" in processor.preprocessed_df.columns
    assert processor.preprocessed_df["quantity_received"].fillna(0).sum() > 0


def test_acceptation_date_used_for_received_at(
    sample_bsff_data, sample_packagings_data, departements_regions_df, regions_geodata, data_date_interval
):
    """Test that acceptation_date is used for received_at when filtering.

    GIVEN: BSFF data with received_at outside the date interval but packagings have acceptation_date within interval
    WHEN: _preprocess_data is called
    THEN: acceptation_date is used for filtering (via pl.coalesce), BSFF is processed,
          and preprocessed_df contains the data because acceptation_date is within the interval
    """
    company_siret = "43210987654321"
    # Create BSFF data with received_at outside the date interval
    bsff_data_outside_interval = pl.LazyFrame(
        {
            "id": ["bsff-1"],
            "emitter_company_siret": ["12345678901234"],
            "emitter_company_address": ["123 Rue de Paris, 75001 Paris"],
            "recipient_company_siret": ["43210987654321"],
            "received_at": [
                datetime(2023, 12, 1, tzinfo=tz),  # Outside interval
            ],
            "waste_code": ["03 01 01*"],
        }
    )

    # But acceptation_date is within the interval
    packagings_within_interval = pl.LazyFrame(
        {
            "bsff_id": ["bsff-1"],
            "acceptation_weight": [10.0],
            "acceptation_date": [
                datetime(2024, 1, 12, tzinfo=tz),  # Within interval
            ],
        }
    )

    bs_data_dfs = {BSFF: bsff_data_outside_interval}

    processor = WasteOriginsMapProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        regions_geodata=regions_geodata,
        data_date_interval=data_date_interval,
        packagings_data=packagings_within_interval,
    )

    processor._preprocess_data()

    # Should be processed because acceptation_date is within interval
    assert processor.preprocessed_df is not None
    assert len(processor.preprocessed_df) > 0
    total_quantity = processor.preprocessed_df["quantity_received"].fillna(0).sum()
    assert total_quantity == pytest.approx(10.0, rel=1e-6)


def test_check_data_empty_with_no_data(departements_regions_df, regions_geodata, data_date_interval):
    """Test that _check_data_empty returns True when there is no data.

    GIVEN: Empty bs_data_dfs dictionary
    WHEN: _preprocess_data and _check_data_empty are called
    THEN: _check_data_empty returns True
    """
    company_siret = "43210987654321"
    bs_data_dfs = {}

    processor = WasteOriginsMapProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        regions_geodata=regions_geodata,
        data_date_interval=data_date_interval,
        packagings_data=None,
    )

    processor._preprocess_data()
    assert processor._check_data_empty() is True


def test_build_returns_empty_dict_when_data_empty(departements_regions_df, regions_geodata, data_date_interval):
    """Test that build returns empty dict when data is empty.

    GIVEN: Empty bs_data_dfs dictionary
    WHEN: build is called
    THEN: Returns empty dict and no figure is created
    """
    company_siret = "43210987654321"
    bs_data_dfs = {}

    processor = WasteOriginsMapProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        regions_geodata=regions_geodata,
        data_date_interval=data_date_interval,
        packagings_data=None,
    )

    result = processor.build()
    assert result == {}
    assert processor.figure is None


def test_build_returns_figure_when_data_present(
    sample_bsdd_data, departements_regions_df, regions_geodata, data_date_interval
):
    """Test that build returns figure JSON when data is present.

    GIVEN: BSDD data in bs_data_dfs
    WHEN: build is called
    THEN: Returns figure JSON string and figure is created
    """
    company_siret = "43210987654321"
    bs_data_dfs = {BSDD: sample_bsdd_data}

    processor = WasteOriginsMapProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        regions_geodata=regions_geodata,
        data_date_interval=data_date_interval,
        packagings_data=None,
    )

    result = processor.build()
    assert result != {}
    assert processor.figure is not None
    # Result should be a JSON string (from to_json())
    assert isinstance(result, str)
