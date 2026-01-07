from datetime import datetime
from zoneinfo import ZoneInfo

import plotly.graph_objects as go
import polars as pl
import pytest

from sheets.constants import BSDA, BSDASRI, BSDD, BSDD_NON_DANGEROUS

from ..graph_processors.plotly_components import IntermediaryBordereauxCountsGraphProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_bs_data_dfs():
    """Fixture for sample bordereau data."""
    return {
        BSDD: pl.LazyFrame(
            {
                "id": ["bsdd-1", "bsdd-2", "bsdd-3"],
                "eco_organisme_siret": [
                    "12345678901234",
                    "12345678901234",
                    "99999999999999",
                ],
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
                "sent_at": [
                    datetime(2024, 1, 15, tzinfo=tz),
                    datetime(2024, 2, 20, tzinfo=tz),
                ],
            }
        ),
        BSDA: pl.LazyFrame(
            {
                "id": ["bsda-1"],
                "eco_organisme_siret": ["12345678901234"],
                "sent_at": [
                    datetime(2024, 1, 15, tzinfo=tz),
                ],
            }
        ),
        BSDASRI: pl.LazyFrame(
            {
                "id": ["bsdasri-1"],
                "eco_organisme_siret": ["12345678901234"],
                "sent_at": [datetime(2024, 3, 15, tzinfo=tz)],
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
    GIVEN bordereau data and transporter data for intermediary bordereaux
    WHEN _preprocess_bs_data is called on IntermediaryBordereauxCountsGraphProcessor
    THEN the processor correctly groups intermediary bordereaux counts by type and month
    """
    processor = IntermediaryBordereauxCountsGraphProcessor(
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

    # Check BSDD counts (only 2 match the company SIRET)
    bsdd_stats = processor.bordereaux_stats[BSDD]
    assert len(bsdd_stats) == 2  # 2 different months
    assert bsdd_stats["id"].sum() == 2  # 2 unique bordereaux


def test_preprocess_bs_data_without_transporters_data(date_interval):
    """
    GIVEN bordereau data without transporter data for BSDD/BSDA types
    WHEN _preprocess_bs_data is called on IntermediaryBordereauxCountsGraphProcessor
    THEN the processor skips types that require transporter data
    """
    bs_data = {
        BSDD: pl.LazyFrame(
            {
                "id": ["bsdd-1"],
                "eco_organisme_siret": ["12345678901234"],
                "sent_at": [datetime(2024, 1, 15, tzinfo=tz)],
            }
        ),
        BSDASRI: pl.LazyFrame(
            {
                "id": ["bsdasri-1"],
                "eco_organisme_siret": ["12345678901234"],
                "sent_at": [datetime(2024, 1, 15, tzinfo=tz)],
            }
        ),
    }
    empty_transporters = {}

    processor = IntermediaryBordereauxCountsGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=bs_data,
        transporters_data_df=empty_transporters,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    # BSDD should be None (requires transporter data)
    assert processor.bordereaux_stats[BSDD] is None
    # BSDASRI should be processed (doesn't require transporter data)
    assert processor.bordereaux_stats[BSDASRI] is not None


def test_check_data_empty(sample_bs_data_dfs, sample_transporters_data, date_interval):
    """
    GIVEN bordereau data and transporter data with matching company SIRET
    WHEN _check_data_empty is called after preprocessing
    THEN it returns False indicating data is not empty
    """
    processor = IntermediaryBordereauxCountsGraphProcessor(
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

    processor = IntermediaryBordereauxCountsGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=empty_bs_data,
        transporters_data_df=empty_transporters,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    assert processor._check_data_empty()


def test_create_figure(sample_bs_data_dfs, sample_transporters_data, date_interval):
    """
    GIVEN preprocessed intermediary bordereaux data
    WHEN _create_figure is called on IntermediaryBordereauxCountsGraphProcessor
    THEN it creates a valid Plotly Figure with stacked bar traces
    """
    processor = IntermediaryBordereauxCountsGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_bs_data_dfs,
        transporters_data_df=sample_transporters_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()
    processor._create_figure()

    assert processor.figure is not None
    assert isinstance(processor.figure, go.Figure)
    assert len(processor.figure.data) > 0  # At least one bar trace


def test_build(sample_bs_data_dfs, sample_transporters_data, date_interval):
    """
    GIVEN bordereau data and transporter data
    WHEN build is called on IntermediaryBordereauxCountsGraphProcessor
    THEN it returns a JSON string representation of the figure
    """
    processor = IntermediaryBordereauxCountsGraphProcessor(
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
    WHEN build is called on IntermediaryBordereauxCountsGraphProcessor
    THEN it returns an empty dict
    """
    empty_bs_data = {
        BSDD: pl.LazyFrame(
            {
                "id": ["bsdd-1"],
                "eco_organisme_siret": ["99999999999999"],
            }
        ),
    }
    empty_transporters = {}

    processor = IntermediaryBordereauxCountsGraphProcessor(
        company_siret="12345678901234",
        bs_data_dfs=empty_bs_data,
        transporters_data_df=empty_transporters,
        data_date_interval=date_interval,
    )
    result = processor.build()

    assert result == {}
