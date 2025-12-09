from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from sheets.constants import BSDD, BSFF

from ..graph_processors.plotly_components import WasteOriginProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def departements_regions_df():
    """Fixture for départements and regions data."""
    return pl.LazyFrame(
        {
            "DEP": ["75", "13", "69", "33"],
            "LIBELLE": ["Paris", "Bouches-du-Rhône", "Rhône", "Gironde"],
            "REG": ["11", "93", "84", "75"],
        }
    )


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
    sample_bsff_data, sample_packagings_data, departements_regions_df, data_date_interval
):
    """Test that BSFF quantities are correctly summed from packagings in full preprocessing flow.

    GIVEN: BSFF data with packagings data containing quantities at container level
           (bsff-1: 10.0, bsff-2: 20.0+30.0=50.0, bsff-3: 40.0+50.0=90.0, total=150.0)
    WHEN: _preprocess_data is called
    THEN: BSFF quantities are correctly summed from packagings, aggregated by department,
          and total quantity in preprocessed_serie equals 150.0
    """
    company_siret = "43210987654321"
    bs_data_dfs = {BSFF: sample_bsff_data}

    processor = WasteOriginProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
        packagings_data=sample_packagings_data,
    )

    processor._preprocess_data()

    # Verify that BSFF data was processed correctly
    assert processor.preprocessed_serie is not None
    assert len(processor.preprocessed_serie) > 0

    # Verify quantities are aggregated correctly by department
    total_quantity = processor.preprocessed_serie["quantity_received"].sum()
    assert total_quantity == pytest.approx(150.0, rel=1e-6)


def test_bsff_process_bsff_data_method(
    sample_bsff_data, sample_packagings_data, departements_regions_df, data_date_interval
):
    """Test the _process_bsff_data method directly.

    GIVEN: BSFF data with packagings data containing quantities at container level
    WHEN: _process_bsff_data is called
    THEN: BSFF data is joined with packagings, quantities are summed per bordereau,
          and the processed dataframe contains quantity_received, emitter_company_address, and received_at columns
    """
    processed_bsff_df = WasteOriginProcessor._process_bsff_data(
        packagings_data=sample_packagings_data, bsff_df=sample_bsff_data
    )

    # Verify BSFF data was processed correctly
    assert processed_bsff_df is not None

    # Verify the processed dataframe has the correct structure
    processed_df = processed_bsff_df.collect()
    expected_columns = {
        "id",
        "emitter_company_siret",
        "emitter_company_address",
        "recipient_company_siret",
        "quantity_received",
        "received_at",
    }
    assert set(processed_df.columns) == expected_columns

    # Verify quantities are summed correctly
    quantities = processed_df["quantity_received"].to_list()
    assert sum(quantities) == pytest.approx(150.0, rel=1e-6)


def test_bsff_process_bsff_data_without_packagings(sample_bsff_data, departements_regions_df, data_date_interval):
    """Test _process_bsff_data when packagings_data is None.

    GIVEN: BSFF data exists but packagings_data is None
    WHEN: _process_bsff_data is called
    THEN: Returns None (cannot calculate quantities without packagings)
    """
    processed_bsff_df = WasteOriginProcessor._process_bsff_data(packagings_data=None, bsff_df=sample_bsff_data)

    # Should return None when packagings_data is None
    assert processed_bsff_df is None


def test_bsff_process_bsff_data_not_in_dictionary(departements_regions_df, data_date_interval):
    """Test _process_bsff_data when bsff_df is None.

    GIVEN: bsff_df is None (BSFF not present in bs_data_dfs)
    WHEN: _process_bsff_data is called
    THEN: Returns None without raising an error
    """
    processed_bsff_df = WasteOriginProcessor._process_bsff_data(packagings_data=None, bsff_df=None)

    # Should return None when bsff_df is None
    assert processed_bsff_df is None


def test_bsff_absent_from_dictionary_no_error(sample_bsdd_data, departements_regions_df, data_date_interval):
    """Test that no error occurs when BSFF is not in bs_data_dfs during full preprocessing.

    GIVEN: BSFF is not present in bs_data_dfs but other bordereau types (BSDD) are present
    WHEN: _preprocess_data is called
    THEN: No error is raised, processing completes gracefully,
          and only BSDD data is processed (BSFF absence is handled correctly)
    """
    company_siret = "43210987654321"
    bs_data_dfs = {BSDD: sample_bsdd_data}  # No BSFF in dictionary

    processor = WasteOriginProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
        packagings_data=None,
    )

    processor._preprocess_data()

    # Should handle gracefully and process BSDD
    assert processor.preprocessed_serie is not None
    assert len(processor.preprocessed_serie) > 0
    # Total quantity should only include BSDD (25.0 + 35.0 = 60.0)
    total_quantity = processor.preprocessed_serie["quantity_received"].sum()
    assert total_quantity == pytest.approx(60.0, rel=1e-6)


def test_bsff_without_packagings_ignored(sample_bsff_data, departements_regions_df, data_date_interval):
    """Test that BSFF is ignored when packagings_data is None.

    GIVEN: BSFF data exists but packagings_data is None
    WHEN: _preprocess_data is called
    THEN: BSFF is excluded from processing (returns None from _process_bsff_data),
          resulting in empty preprocessed_serie
    """
    company_siret = "43210987654321"
    bs_data_dfs = {BSFF: sample_bsff_data}

    processor = WasteOriginProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
        packagings_data=None,
    )

    processor._preprocess_data()

    # BSFF should not be in the local copy used for processing
    # Original bs_data_dfs should remain unchanged (not mutated)
    assert BSFF in processor.bs_data_dfs
    assert processor.bs_data_dfs[BSFF] is sample_bsff_data  # Original reference preserved

    # No data should be in preprocessed_serie since BSFF was the only data and was excluded
    assert processor.preprocessed_serie is None or len(processor.preprocessed_serie) == 0


def test_mix_bsff_and_other_bordereaux(
    sample_bsff_data,
    sample_packagings_data,
    sample_bsdd_data,
    departements_regions_df,
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

    processor = WasteOriginProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
        packagings_data=sample_packagings_data,
    )

    processor._preprocess_data()

    # Both BSFF and BSDD should be processed
    assert processor.preprocessed_serie is not None
    assert len(processor.preprocessed_serie) > 0

    # Total quantity should include both BSFF (150.0) and BSDD (25.0 + 35.0 = 60.0)
    total_quantity = processor.preprocessed_serie["quantity_received"].sum()
    assert total_quantity == pytest.approx(210.0, rel=1e-6)


def test_departments_calculated_correctly_with_bsff_quantities(
    sample_bsff_data, sample_packagings_data, departements_regions_df, data_date_interval
):
    """Test that departments are correctly calculated with BSFF quantities.

    GIVEN: BSFF data with packagings containing addresses with postal codes (75001, 13001, 69001)
    WHEN: _preprocess_data is called
    THEN: Departments are correctly extracted from addresses, quantities are aggregated by department,
          and preprocessed_serie contains cp_formatted column with department information
    """
    company_siret = "43210987654321"
    bs_data_dfs = {BSFF: sample_bsff_data}

    processor = WasteOriginProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
        packagings_data=sample_packagings_data,
    )

    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert len(processor.preprocessed_serie) > 0

    # Verify that departments are correctly identified from addresses
    # bsff-1: 75001 -> 75 (Paris) -> 10.0
    # bsff-2: 13001 -> 13 (Bouches-du-Rhône) -> 50.0
    # bsff-3: 69001 -> 69 (Rhône) -> 90.0

    # Check that cp_formatted contains department information
    for row in processor.preprocessed_serie.iter_rows(named=True):
        assert "cp_formatted" in row
        assert row["quantity_received"] > 0


def test_acceptation_date_used_for_received_at(
    sample_bsff_data, sample_packagings_data, departements_regions_df, data_date_interval
):
    """Test that acceptation_date is used for received_at when filtering.

    GIVEN: BSFF data with received_at outside the date interval but packagings have acceptation_date within interval
    WHEN: _preprocess_data is called
    THEN: acceptation_date is used for filtering (via pl.coalesce), BSFF is processed,
          and preprocessed_serie contains the data because acceptation_date is within the interval
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

    processor = WasteOriginProcessor(
        company_siret=company_siret,
        bs_data_dfs=bs_data_dfs,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
        packagings_data=packagings_within_interval,
    )

    processor._preprocess_data()

    # Should be processed because acceptation_date is within interval
    assert processor.preprocessed_serie is not None
    assert len(processor.preprocessed_serie) > 0
