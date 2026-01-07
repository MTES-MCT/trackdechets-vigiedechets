from datetime import datetime
from zoneinfo import ZoneInfo

import plotly.graph_objects as go
import polars as pl
import pytest

from sheets.constants import BSDA, BSDASRI, BSDD, BSDD_NON_DANGEROUS

from ..graph_processors.plotly_components import IntermediaryBordereauxQuantitiesGraphProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_bs_data_dfs():
    """Fixture for sample bordereau data with quantities."""
    return {
        BSDD: pl.LazyFrame(
            {
                "id": ["bsdd-1", "bsdd-2", "bsdd-3"],
                "eco_organisme_siret": [
                    "12345678901234",
                    "12345678901234",
                    "99999999999999",
                ],
                "quantity_received": [10.0, 20.0, 15.0],
                "quantity_refused": [0.0, 2.0, 0.0],
                "sent_at": [
                    datetime(2024, 1, 15, tzinfo=tz),
                    datetime(2024, 2, 10, tzinfo=tz),
                    datetime(2024, 2, 20, tzinfo=tz),
                ],
            }
        ),
        BSDD_NON_DANGEROUS: pl.LazyFrame(
            {
                "id": ["bsdd-nd-1", "bsdd-nd-2"],
                "eco_organisme_siret": [
                    "12345678901234",
                    "12345678901234",
                ],
                "quantity_received": [5.0, 8.0],
                "quantity_refused": [0.0, 1.0],
                "sent_at": [
                    datetime(2024, 1, 20, tzinfo=tz),
                    datetime(2024, 3, 5, tzinfo=tz),
                ],
            }
        ),
        BSDA: pl.LazyFrame(
            {
                "id": ["bsda-1"],
                "eco_organisme_siret": ["12345678901234"],
                "quantity_received": [3.5],
                "sent_at": [datetime(2024, 3, 10, tzinfo=tz)],
            }
        ),
        BSDASRI: pl.LazyFrame(
            {
                "id": ["bsdasri-1"],
                "eco_organisme_siret": ["12345678901234"],
                "quantity_received": [2.0],
                "quantity_refused": [0.0],
                "sent_at": [datetime(2024, 1, 15, tzinfo=tz)],
            }
        ),
    }


@pytest.fixture
def sample_transporters_data():
    """Fixture for sample transporter data."""
    return {
        BSDD: pl.LazyFrame(
            {
                "bs_id": ["bsdd-1", "bsdd-2", "bsdd-3"],
                "sent_at": [
                    datetime(2024, 1, 15, tzinfo=tz),
                    datetime(2024, 2, 10, tzinfo=tz),
                    datetime(2024, 2, 20, tzinfo=tz),
                ],
            }
        ),
        BSDD_NON_DANGEROUS: pl.LazyFrame(
            {
                "bs_id": ["bsdd-nd-1", "bsdd-nd-2"],
                "sent_at": [
                    datetime(2024, 1, 20, tzinfo=tz),
                    datetime(2024, 3, 5, tzinfo=tz),
                ],
            }
        ),
        BSDA: pl.LazyFrame(
            {
                "bs_id": ["bsda-1"],
                "sent_at": [datetime(2024, 3, 10, tzinfo=tz)],
            }
        ),
    }


@pytest.fixture
def date_interval():
    """Fixture for the date interval."""
    return (datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 3, 31, tzinfo=tz))


def test_preprocess_bs_data(sample_bs_data_dfs, sample_transporters_data, date_interval):
    """
    GIVEN bordereau data and transporter data for intermediary bordereaux with quantities
    WHEN _preprocess_bs_data is called on IntermediaryBordereauxQuantitiesGraphProcessor
    THEN the processor correctly groups intermediary quantities by type and month, subtracting refused quantities
    """
    processor = IntermediaryBordereauxQuantitiesGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_bs_data_dfs,
        transporters_data_df=sample_transporters_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    # Check that stats are populated for bordereau types with data
    assert processor.bordereaux_stats[BSDD] is not None
    assert processor.bordereaux_stats[BSDD_NON_DANGEROUS] is not None
    assert processor.bordereaux_stats[BSDA] is not None
    assert processor.bordereaux_stats[BSDASRI] is not None

    # Check BSDD quantities (only 2 match the company SIRET)
    # bsdd-1: 10.0 - 0.0 = 10.0
    # bsdd-2: 20.0 - 2.0 = 18.0
    bsdd_stats = processor.bordereaux_stats[BSDD]
    assert len(bsdd_stats) == 2  # 2 different months
    assert bsdd_stats["quantity_received"].sum() == pytest.approx(28.0, rel=1e-6)  # 10.0 + 18.0


def test_quantity_calculation_with_refused(sample_bs_data_dfs, sample_transporters_data, date_interval):
    """
    GIVEN bordereau data with quantity_received and quantity_refused
    WHEN _preprocess_bs_data is called on IntermediaryBordereauxQuantitiesGraphProcessor
    THEN the processor correctly calculates net quantity (quantity_received - quantity_refused)
    """
    processor = IntermediaryBordereauxQuantitiesGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_bs_data_dfs,
        transporters_data_df=sample_transporters_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    # Check BSDD_NON_DANGEROUS quantities
    # bsdd-nd-1: 5.0 - 0.0 = 5.0
    # bsdd-nd-2: 8.0 - 1.0 = 7.0
    bsdd_nd_stats = processor.bordereaux_stats[BSDD_NON_DANGEROUS]
    assert bsdd_nd_stats["quantity_received"].sum() == pytest.approx(12.0, rel=1e-6)  # 5.0 + 7.0


def test_check_data_empty(sample_bs_data_dfs, sample_transporters_data, date_interval):
    """
    GIVEN bordereau data and transporter data with matching company SIRET
    WHEN _check_data_empty is called after preprocessing
    THEN it returns False indicating data is not empty
    """
    processor = IntermediaryBordereauxQuantitiesGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_bs_data_dfs,
        transporters_data_df=sample_transporters_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    assert not processor._check_data_empty()


def test_check_data_empty_with_no_matching_data(date_interval):
    """
    GIVEN bordereau data with no matching company SIRET
    WHEN _check_data_empty is called after preprocessing
    THEN it returns True indicating data is empty
    """
    empty_bs_data = {
        BSDD: pl.LazyFrame(
            {
                "id": ["bsdd-1"],
                "eco_organisme_siret": ["99999999999999"],
                "quantity_received": [10.0],
                "quantity_refused": [0.0],
            }
        ),
    }
    empty_transporters = {
        BSDD: pl.LazyFrame(
            {
                "bs_id": ["bsdd-1"],
                "sent_at": [datetime(2024, 1, 15, tzinfo=tz)],
            }
        ),
    }

    processor = IntermediaryBordereauxQuantitiesGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=empty_bs_data,
        transporters_data_df=empty_transporters,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    assert processor._check_data_empty()


def test_create_figure(sample_bs_data_dfs, sample_transporters_data, date_interval):
    """
    GIVEN preprocessed intermediary bordereaux quantities data
    WHEN _create_figure is called on IntermediaryBordereauxQuantitiesGraphProcessor
    THEN it creates a valid Plotly Figure with line traces using stackgroup
    """
    processor = IntermediaryBordereauxQuantitiesGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_bs_data_dfs,
        transporters_data_df=sample_transporters_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()
    processor._create_figure()

    assert processor.figure is not None
    assert isinstance(processor.figure, go.Figure)
    assert len(processor.figure.data) > 0  # At least one line trace


def test_build(sample_bs_data_dfs, sample_transporters_data, date_interval):
    """
    GIVEN bordereau data and transporter data with quantities
    WHEN build is called on IntermediaryBordereauxQuantitiesGraphProcessor
    THEN it returns a JSON string representation of the figure
    """
    processor = IntermediaryBordereauxQuantitiesGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_bs_data_dfs,
        transporters_data_df=sample_transporters_data,
        data_date_interval=date_interval,
    )
    result = processor.build()

    assert isinstance(result, str)
    assert len(result) > 0
    assert "data" in result


def test_build_with_empty_data(date_interval):
    """
    GIVEN bordereau data with no matching company SIRET
    WHEN build is called on IntermediaryBordereauxQuantitiesGraphProcessor
    THEN it returns an empty dict
    """
    empty_bs_data = {
        BSDD: pl.LazyFrame(
            {
                "id": ["bsdd-1"],
                "eco_organisme_siret": ["99999999999999"],
                "quantity_received": [10.0],
                "quantity_refused": [0.0],
            }
        ),
    }
    empty_transporters = {}

    processor = IntermediaryBordereauxQuantitiesGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=empty_bs_data,
        transporters_data_df=empty_transporters,
        data_date_interval=date_interval,
    )
    result = processor.build()

    assert result == {}
