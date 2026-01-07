from datetime import datetime
from zoneinfo import ZoneInfo

import plotly.graph_objects as go
import polars as pl
import pytest

from sheets.constants import BSDA, BSDASRI, BSDD, BSFF, BSVHU

from ..graph_processors.plotly_components import TransporterBordereauxGraphProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_transporters_data():
    """Fixture for sample transporter data."""
    return {
        BSDD: pl.LazyFrame(
            {
                "bs_id": ["bsdd-1", "bsdd-2", "bsdd-3"],
                "transporter_company_siret": [
                    "12345678901234",
                    "12345678901234",
                    "12345678901234",
                ],
                "sent_at": [
                    datetime(2024, 1, 15, tzinfo=tz),
                    datetime(2024, 2, 10, tzinfo=tz),
                    datetime(2024, 2, 20, tzinfo=tz),
                ],
            }
        ),
        BSDA: pl.LazyFrame(
            {
                "bs_id": ["bsda-1", "bsda-2"],
                "transporter_company_siret": [
                    "12345678901234",
                    "12345678901234",
                ],
                "sent_at": [
                    datetime(2024, 1, 20, tzinfo=tz),
                    datetime(2024, 3, 5, tzinfo=tz),
                ],
            }
        ),
    }


@pytest.fixture
def sample_bs_data_dfs():
    """Fixture for sample bordereau data."""
    return {
        BSFF: pl.LazyFrame(
            {
                "bs_id": ["bsff-1", "bsff-2"],
                "id": ["bsff-1", "bsff-2"],
                "transporter_company_siret": [
                    "12345678901234",
                    "12345678901234",
                ],
                "sent_at": [
                    datetime(2024, 2, 15, tzinfo=tz),
                    datetime(2024, 3, 10, tzinfo=tz),
                ],
            }
        ),
        BSDASRI: pl.LazyFrame(
            {
                "bs_id": ["bsdasri-1"],
                "id": ["bsdasri-1"],
                "transporter_company_siret": ["12345678901234"],
                "sent_at": [datetime(2024, 3, 15, tzinfo=tz)],
            }
        ),
        BSVHU: pl.LazyFrame(
            {
                "bs_id": ["bsvhu-1"],
                "id": ["bsvhu-1"],
                "transporter_company_siret": ["12345678901234"],
                "sent_at": [datetime(2024, 3, 20, tzinfo=tz)],
            }
        ),
    }


@pytest.fixture
def date_interval():
    """Fixture for the date interval."""
    return (datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 3, 31, tzinfo=tz))


def test_preprocess_bs_data(sample_transporters_data, sample_bs_data_dfs, date_interval):
    """
    GIVEN transporter data and bordereau data for multiple bordereau types
    WHEN _preprocess_bs_data is called on TransporterBordereauxGraphProcessor
    THEN the processor correctly groups bordereaux counts by type and month
    """
    processor = TransporterBordereauxGraphProcessor(
        company_siret="12345678901234",
        transporters_data_df=sample_transporters_data,
        bs_data_dfs=sample_bs_data_dfs,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    # Check that stats are populated for bordereau types with data
    assert processor.transported_bordereaux_stats[BSDD] is not None
    assert processor.transported_bordereaux_stats[BSDA] is not None
    assert processor.transported_bordereaux_stats[BSFF] is not None
    assert processor.transported_bordereaux_stats[BSDASRI] is not None
    assert processor.transported_bordereaux_stats[BSVHU] is not None

    # Check BSDD counts
    bsdd_stats = processor.transported_bordereaux_stats[BSDD]
    assert len(bsdd_stats) == 2  # 2 different months
    assert bsdd_stats["bs_count"].sum() == 3  # 3 unique bordereaux


def test_check_data_empty(sample_transporters_data, sample_bs_data_dfs, date_interval):
    """
    GIVEN transporter data and bordereau data with matching company SIRET
    WHEN _check_data_empty is called after preprocessing
    THEN it returns False indicating data is not empty
    """
    processor = TransporterBordereauxGraphProcessor(
        company_siret="12345678901234",
        transporters_data_df=sample_transporters_data,
        bs_data_dfs=sample_bs_data_dfs,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    assert not processor._check_data_empty()


def test_check_data_empty_with_no_matching_data(date_interval):
    """
    GIVEN transporter data and bordereau data with no matching company SIRET
    WHEN _check_data_empty is called after preprocessing
    THEN it returns True indicating data is empty
    """
    empty_transporters = {
        BSDD: pl.LazyFrame(
            {
                "bs_id": ["bsdd-1"],
                "transporter_company_siret": ["99999999999999"],
                "sent_at": [datetime(2024, 1, 15, tzinfo=tz)],
            }
        ),
    }
    empty_bs_data = {
        BSFF: pl.LazyFrame(
            {
                "bs_id": ["bsff-1"],
                "transporter_company_siret": ["99999999999999"],
                "sent_at": [datetime(2024, 1, 15, tzinfo=tz)],
            }
        ),
    }

    processor = TransporterBordereauxGraphProcessor(
        company_siret="12345678901234",
        transporters_data_df=empty_transporters,
        bs_data_dfs=empty_bs_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    assert processor._check_data_empty()


def test_create_figure(sample_transporters_data, sample_bs_data_dfs, date_interval):
    """
    GIVEN preprocessed transporter bordereaux data
    WHEN _create_figure is called on TransporterBordereauxGraphProcessor
    THEN it creates a valid Plotly Figure with stacked bar traces
    """
    processor = TransporterBordereauxGraphProcessor(
        company_siret="12345678901234",
        transporters_data_df=sample_transporters_data,
        bs_data_dfs=sample_bs_data_dfs,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()
    processor._create_figure()

    assert processor.figure is not None
    assert isinstance(processor.figure, go.Figure)
    assert len(processor.figure.data) > 0  # At least one bar trace


def test_build(sample_transporters_data, sample_bs_data_dfs, date_interval):
    """
    GIVEN transporter data and bordereau data
    WHEN build is called on TransporterBordereauxGraphProcessor
    THEN it returns a JSON string representation of the figure
    """
    processor = TransporterBordereauxGraphProcessor(
        company_siret="12345678901234",
        transporters_data_df=sample_transporters_data,
        bs_data_dfs=sample_bs_data_dfs,
        data_date_interval=date_interval,
    )
    result = processor.build()

    assert isinstance(result, str)
    assert len(result) > 0
    assert "data" in result


def test_build_with_empty_data(date_interval):
    """
    GIVEN transporter data and bordereau data with no matching company SIRET
    WHEN build is called on TransporterBordereauxGraphProcessor
    THEN it returns an empty dict
    """
    empty_transporters = {
        BSDD: pl.LazyFrame(
            {
                "bs_id": ["bsdd-1"],
                "transporter_company_siret": ["99999999999999"],
                "sent_at": [datetime(2024, 1, 15, tzinfo=tz)],
            }
        ),
    }
    empty_bs_data = {}

    processor = TransporterBordereauxGraphProcessor(
        company_siret="12345678901234",
        transporters_data_df=empty_transporters,
        bs_data_dfs=empty_bs_data,
        data_date_interval=date_interval,
    )
    result = processor.build()

    assert result == {}


def test_multiple_bordereau_types(sample_transporters_data, sample_bs_data_dfs, date_interval):
    """
    GIVEN transporter data and bordereau data for multiple bordereau types
    WHEN _preprocess_bs_data is called on TransporterBordereauxGraphProcessor
    THEN the processor correctly processes all bordereau types (BSDD, BSDA, BSFF, BSDASRI, BSVHU)
    """
    processor = TransporterBordereauxGraphProcessor(
        company_siret="12345678901234",
        transporters_data_df=sample_transporters_data,
        bs_data_dfs=sample_bs_data_dfs,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    # Verify all types are processed
    assert processor.transported_bordereaux_stats[BSDD] is not None
    assert processor.transported_bordereaux_stats[BSDA] is not None
    assert processor.transported_bordereaux_stats[BSFF] is not None
    assert processor.transported_bordereaux_stats[BSDASRI] is not None
    assert processor.transported_bordereaux_stats[BSVHU] is not None
