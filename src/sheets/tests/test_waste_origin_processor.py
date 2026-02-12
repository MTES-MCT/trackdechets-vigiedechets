from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from sheets.constants import DANGEROUS_WASTE, NON_DANGEROUS_WASTE

from ..graph_processors.plotly_components import WasteOriginProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def departements_regions_df():
    """Fixture for departements and regions data."""
    return pl.LazyFrame(
        {
            "DEP": ["75", "13", "69", "33"],
            "LIBELLE": ["Paris", "Bouches-du-Rhone", "Rhone", "Gironde"],
            "REG": ["11", "93", "84", "75"],
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


def test_dangerous_waste_type(sample_bsdd_data, departements_regions_df, data_date_interval):
    """Test that BSDD data is processed correctly with the dangerous waste type.

    GIVEN: BSDD data with two bordereaux (25.0 + 35.0 = 60.0)
    WHEN: _preprocess_data is called with waste_type=DANGEROUS_WASTE
    THEN: Data is processed correctly, total quantity = 60.0
    """
    company_siret = "43210987654321"

    processor = WasteOriginProcessor(
        company_siret=company_siret,
        waste_type=DANGEROUS_WASTE,
        bs_data_df=sample_bsdd_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )

    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert len(processor.preprocessed_serie) > 0
    total_quantity = processor.preprocessed_serie["quantity_received"].sum()
    assert total_quantity == pytest.approx(60.0, rel=1e-6)


def test_non_dangerous_waste_type(departements_regions_df, data_date_interval):
    """Test that non-dangerous waste data is processed correctly.

    GIVEN: BSDD non-dangerous data with two bordereaux (15.0 + 25.0 = 40.0)
    WHEN: _preprocess_data is called with waste_type=NON_DANGEROUS_WASTE
    THEN: Data is processed correctly, total quantity = 40.0
    """
    company_siret = "43210987654321"

    bsdd_non_dangerous_data = pl.LazyFrame(
        {
            "id": ["bsdd-nd-1", "bsdd-nd-2"],
            "emitter_company_siret": ["11111111111111", "22222222222222"],
            "emitter_company_address": [
                "10 Rue Bordeaux, 33000 Bordeaux",
                "20 Rue Paris, 75002 Paris",
            ],
            "recipient_company_siret": [company_siret, company_siret],
            "received_at": [
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 2, 20, tzinfo=tz),
            ],
            "quantity_received": [15.0, 25.0],
            "waste_code": ["01 01 01", "01 01 02"],
        }
    )

    processor = WasteOriginProcessor(
        company_siret=company_siret,
        waste_type=NON_DANGEROUS_WASTE,
        bs_data_df=bsdd_non_dangerous_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )

    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert len(processor.preprocessed_serie) > 0
    total_quantity = processor.preprocessed_serie["quantity_received"].sum()
    assert total_quantity == pytest.approx(40.0, rel=1e-6)


def test_departments_calculated_correctly(sample_bsdd_data, departements_regions_df, data_date_interval):
    """Test that departments are correctly calculated with waste quantities.

    GIVEN: BSDD data with addresses containing postal codes (33000, 75002)
    WHEN: _preprocess_data is called with waste_type=DANGEROUS_WASTE
    THEN: Departments are correctly extracted from addresses, quantities are aggregated by department,
          and preprocessed_serie contains cp_formatted column with department information
    """
    company_siret = "43210987654321"

    processor = WasteOriginProcessor(
        company_siret=company_siret,
        waste_type=DANGEROUS_WASTE,
        bs_data_df=sample_bsdd_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )

    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert len(processor.preprocessed_serie) > 0

    for row in processor.preprocessed_serie.iter_rows(named=True):
        assert "cp_formatted" in row
        assert row["quantity_received"] > 0


def test_top_10_departments_kept(departements_regions_df, data_date_interval):
    """Test that only top 10 departments are kept, rest grouped as 'Autres origines'.

    GIVEN: BSDD data with 12 different departments
    WHEN: _preprocess_data is called
    THEN: Only top 10 departments are kept individually,
          remaining departments are grouped under 'Autres origines'
    """
    company_siret = "43210987654321"

    departements_df = pl.LazyFrame(
        {
            "DEP": [f"{i:02d}" for i in range(1, 13)],
            "LIBELLE": [f"Dep{i}" for i in range(1, 13)],
            "REG": ["01"] * 12,
        }
    )

    addresses = [f"1 Rue, {i:02d}000 Ville" for i in range(1, 13)]
    quantities = [float(i * 10) for i in range(1, 13)]

    bsdd_data = pl.LazyFrame(
        {
            "id": [f"bsdd-{i}" for i in range(1, 13)],
            "emitter_company_siret": ["11111111111111"] * 12,
            "emitter_company_address": addresses,
            "recipient_company_siret": [company_siret] * 12,
            "received_at": [datetime(2024, 1, 15, tzinfo=tz)] * 12,
            "quantity_received": quantities,
            "waste_code": ["01 01 01*"] * 12,
        }
    )

    processor = WasteOriginProcessor(
        company_siret=company_siret,
        waste_type=DANGEROUS_WASTE,
        bs_data_df=bsdd_data,
        departements_regions_df=departements_df,
        data_date_interval=data_date_interval,
    )

    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    departments = processor.preprocessed_serie["cp_formatted"].to_list()
    assert "Autres origines" in departments
    # 10 individual departments + 1 "Autres origines" = 11
    assert len(departments) == 11
