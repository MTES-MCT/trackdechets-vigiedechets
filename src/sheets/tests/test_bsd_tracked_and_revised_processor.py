from datetime import datetime
from zoneinfo import ZoneInfo

import plotly.graph_objects as go
import polars as pl
import pytest
from polars.testing import assert_frame_equal

from ..graph_processors.plotly_components import BsdTrackedAndRevisedProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_bs_data():
    """Fixture for sample bordereau data."""
    return pl.LazyFrame(
        {
            "id": ["bs-1", "bs-2", "bs-3", "bs-4", "bs-5"],
            "emitter_company_siret": [
                "12345678901234",
                "12345678901234",
                "98765432109876",
                "12345678901234",
                "98765432109876",
            ],
            "recipient_company_siret": [
                "98765432109876",
                "98765432109876",
                "12345678901234",
                "98765432109876",
                "12345678901234",
            ],
            "sent_at": [
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 2, 10, tzinfo=tz),
                datetime(2024, 2, 20, tzinfo=tz),
                datetime(2024, 3, 5, tzinfo=tz),
                datetime(2024, 3, 15, tzinfo=tz),
            ],
            "received_at": [
                datetime(2024, 1, 20, tzinfo=tz),
                datetime(2024, 2, 15, tzinfo=tz),
                datetime(2024, 2, 25, tzinfo=tz),
                datetime(2024, 3, 10, tzinfo=tz),
                datetime(2024, 3, 20, tzinfo=tz),
            ],
        }
    )


@pytest.fixture
def sample_revised_data():
    """Fixture for sample revised bordereau data."""
    return pl.LazyFrame(
        {
            "bs_id": ["bs-1", "bs-2", "bs-4"],
            "created_at": [
                datetime(2024, 1, 25, tzinfo=tz),
                datetime(2024, 2, 18, tzinfo=tz),
                datetime(2024, 3, 12, tzinfo=tz),
            ],
        }
    )


@pytest.fixture
def date_interval():
    """Fixture for the date interval."""
    return (datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 3, 31, tzinfo=tz))


def test_preprocess_bs_data(sample_bs_data, date_interval):
    """
    GIVEN bordereau data with emitted and received bordereaux for a company
    WHEN _preprocess_bs_data is called on BsdTrackedAndRevisedProcessor
    THEN the processor correctly groups emitted and received bordereaux by month
    """
    processor = BsdTrackedAndRevisedProcessor(
        company_siret="12345678901234",
        bs_data=sample_bs_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    assert processor.bs_emitted_by_month is not None
    assert processor.bs_received_by_month is not None

    # Check emitted bordereaux: bs-1, bs-2, bs-4 (3 total)
    emitted_df = processor.bs_emitted_by_month
    assert len(emitted_df) == 3  # 3 different months
    assert emitted_df["id"].sum() == 3  # 3 unique bordereaux

    # Check received bordereaux: bs-3, bs-5 (2 total)
    received_df = processor.bs_received_by_month
    assert len(received_df) == 2  # 2 different months
    assert received_df["id"].sum() == 2  # 2 unique bordereaux


def test_preprocess_bs_revised_data(sample_bs_data, sample_revised_data, date_interval):
    """
    GIVEN bordereau data and revised bordereau data
    WHEN _preprocess_bs_revised_data is called on BsdTrackedAndRevisedProcessor
    THEN the processor correctly groups revised bordereaux by month
    """
    processor = BsdTrackedAndRevisedProcessor(
        company_siret="12345678901234",
        bs_data=sample_bs_data,
        data_date_interval=date_interval,
        bs_revised_data=sample_revised_data,
    )
    processor._preprocess_bs_data()
    processor._preprocess_bs_revised_data()

    assert processor.bs_revised_by_month is not None
    revised_df = processor.bs_revised_by_month
    assert len(revised_df) == 3  # 3 different months
    assert revised_df["bs_id"].sum() == 3  # 3 unique revised bordereaux


def test_preprocess_bs_revised_data_without_revised_data(sample_bs_data, date_interval):
    """
    GIVEN bordereau data without revised data (None)
    WHEN _preprocess_bs_revised_data is called on BsdTrackedAndRevisedProcessor
    THEN the processor handles None gracefully and does not set bs_revised_by_month
    """
    processor = BsdTrackedAndRevisedProcessor(
        company_siret="12345678901234",
        bs_data=sample_bs_data,
        data_date_interval=date_interval,
        bs_revised_data=None,
    )
    processor._preprocess_bs_data()
    processor._preprocess_bs_revised_data()

    assert processor.bs_revised_by_month is None


def test_check_data_empty(sample_bs_data, date_interval):
    """
    GIVEN bordereau data with matching company SIRET
    WHEN _check_data_empty is called after preprocessing
    THEN it returns False indicating data is not empty
    """
    processor = BsdTrackedAndRevisedProcessor(
        company_siret="12345678901234",
        bs_data=sample_bs_data,
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
    empty_data = pl.LazyFrame(
        {
            "id": ["bs-1"],
            "emitter_company_siret": ["99999999999999"],
            "recipient_company_siret": ["88888888888888"],
            "sent_at": [datetime(2024, 1, 15, tzinfo=tz)],
            "received_at": [datetime(2024, 1, 20, tzinfo=tz)],
        }
    )

    processor = BsdTrackedAndRevisedProcessor(
        company_siret="12345678901234",
        bs_data=empty_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    assert processor._check_data_empty()


def test_create_figure(sample_bs_data, date_interval):
    """
    GIVEN preprocessed bordereau data
    WHEN _create_figure is called on BsdTrackedAndRevisedProcessor
    THEN it creates a valid Plotly Figure with bar traces
    """
    processor = BsdTrackedAndRevisedProcessor(
        company_siret="12345678901234",
        bs_data=sample_bs_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()
    processor._create_figure()

    assert processor.figure is not None
    assert isinstance(processor.figure, go.Figure)
    assert len(processor.figure.data) >= 2  # At least emitted and received bars


def test_create_figure_with_revised_data(sample_bs_data, sample_revised_data, date_interval):
    """
    GIVEN preprocessed bordereau data with revised data
    WHEN _create_figure is called on BsdTrackedAndRevisedProcessor
    THEN it creates a valid Plotly Figure with three bar traces (emitted, received, revised)
    """
    processor = BsdTrackedAndRevisedProcessor(
        company_siret="12345678901234",
        bs_data=sample_bs_data,
        data_date_interval=date_interval,
        bs_revised_data=sample_revised_data,
    )
    processor._preprocess_bs_data()
    processor._preprocess_bs_revised_data()
    processor._create_figure()

    assert processor.figure is not None
    assert isinstance(processor.figure, go.Figure)
    assert len(processor.figure.data) == 3  # Emitted, received, and revised bars


def test_build(sample_bs_data, date_interval):
    """
    GIVEN bordereau data
    WHEN build is called on BsdTrackedAndRevisedProcessor
    THEN it returns a JSON string representation of the figure
    """
    processor = BsdTrackedAndRevisedProcessor(
        company_siret="12345678901234",
        bs_data=sample_bs_data,
        data_date_interval=date_interval,
    )
    result = processor.build()

    assert isinstance(result, str)
    assert len(result) > 0
    assert "data" in result


def test_build_with_empty_data(date_interval):
    """
    GIVEN bordereau data with no matching company SIRET
    WHEN build is called on BsdTrackedAndRevisedProcessor
    THEN it returns an empty dict
    """
    empty_data = pl.LazyFrame(
        {
            "id": ["bs-1"],
            "emitter_company_siret": ["99999999999999"],
            "recipient_company_siret": ["88888888888888"],
            "sent_at": [datetime(2024, 1, 15, tzinfo=tz)],
            "received_at": [datetime(2024, 1, 20, tzinfo=tz)],
        }
    )

    processor = BsdTrackedAndRevisedProcessor(
        company_siret="12345678901234",
        bs_data=empty_data,
        data_date_interval=date_interval,
    )
    result = processor.build()

    assert result == {}


def test_build_with_revised_data(sample_bs_data, sample_revised_data, date_interval):
    """
    GIVEN bordereau data with revised data
    WHEN build is called on BsdTrackedAndRevisedProcessor
    THEN it returns a JSON string representation of the figure including revised bordereaux
    """
    processor = BsdTrackedAndRevisedProcessor(
        company_siret="12345678901234",
        bs_data=sample_bs_data,
        data_date_interval=date_interval,
        bs_revised_data=sample_revised_data,
    )
    result = processor.build()

    assert isinstance(result, str)
    assert len(result) > 0
    assert "data" in result

