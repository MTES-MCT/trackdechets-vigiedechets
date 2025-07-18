from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from plotly.graph_objects import Figure
from polars.testing import assert_frame_equal

from ..graph_processors.plotly_components_processors import (
    BsdaWorkerQuantityProcessor,
)  # Replace with actual module name

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def bsda_data():
    """Fixture for sample BSDA data."""
    return pl.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "worker_company_siret": [
                "12345678900001",
                "12345678900001",
                "12345678900002",
                "12345678900001",
                "12345678900001",
            ],
            "waste_details_quantity": [10.5, 20, 30.5, 15, 5.9],
            "quantity_received": [9.0, 20.5, 18.0, 14.5, 6.1],
            "sent_at": [
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 2, 15, tzinfo=tz),
                datetime(2024, 3, 15, tzinfo=tz),
                datetime(2024, 4, 15, tzinfo=tz),
                datetime(2024, 5, 15, tzinfo=tz),
            ],
            "processed_at": [
                datetime(2024, 2, 1, tzinfo=tz),
                datetime(2024, 3, 1, tzinfo=tz),
                None,
                datetime(2024, 5, 1, tzinfo=tz),
                datetime(2024, 6, 1, tzinfo=tz),
            ],
            "worker_work_signature_date": [
                None,
                datetime(2024, 2, 1, tzinfo=tz),
                datetime(2024, 3, 1, tzinfo=tz),
                datetime(2024, 4, 1, tzinfo=tz),
                datetime(2024, 5, 1, tzinfo=tz),
            ],
        }
    ).lazy()


@pytest.fixture
def transporters_data():
    """Fixture for sample transporter data."""
    return pl.DataFrame(
        {
            "bs_id": [1, 2, 3, 4, 5],
            "quantity_received": [9.0, 20.5, 18.0, 14.5, 6.1],
            "sent_at": [
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 2, 15, tzinfo=tz),
                datetime(2024, 4, 15, tzinfo=tz),
                datetime(2024, 5, 15, tzinfo=tz),
            ],
            "transporter_company_siret": [
                "98765432100001",
                "98765432100001",
                "98765432100002",
                "98765432100001",
                "98765432100002",
            ],
        }
    ).lazy()


@pytest.fixture
def date_interval():
    """Fixture for the date interval."""
    return (datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 5, 31, tzinfo=tz))


def test_preprocess_bs_data(bsda_data, transporters_data, date_interval):
    """Test preprocessing of BSDA data."""
    processor = BsdaWorkerQuantityProcessor(
        company_siret="12345678900001",
        bsda_data_df=bsda_data,
        bsda_transporters_data_df=transporters_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    assert processor.quantities_signed_by_worker_by_month is not None
    assert processor.quantities_transported_by_month is not None
    assert processor.quantities_processed_by_month is not None

    # Validate values
    expected_value = pl.DataFrame(
        {
            "date": [
                datetime(2024, 2, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2024, 4, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2024, 5, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
            ],
            "quantity_received": [20.0, 15.0, 5.9],
        }
    )
    assert_frame_equal(processor.quantities_signed_by_worker_by_month, expected_value)

    expected_value = pl.DataFrame(
        {
            "date": [
                datetime(2024, 1, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2024, 4, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2024, 5, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
            ],
            "quantity_received": [29.5, 14.5, 6.1],
        }
    )
    assert_frame_equal(processor.quantities_transported_by_month, expected_value)

    expected_value = pl.DataFrame(
        {
            "date": [
                datetime(2024, 2, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2024, 3, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2024, 5, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
            ],
            "quantity_received": [9.0, 20.5, 14.5],
        }
    )
    assert_frame_equal(processor.quantities_processed_by_month, expected_value)  # Total waste processed


def test_check_data_empty(bsda_data, transporters_data, date_interval):
    """Test check if data is empty."""
    processor = BsdaWorkerQuantityProcessor(
        company_siret="12345678900001",
        bsda_data_df=bsda_data,
        bsda_transporters_data_df=transporters_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()

    assert not processor._check_data_empty()  # Data should not be empty

    # Test with no matching data
    empty_processor = BsdaWorkerQuantityProcessor(
        company_siret="99999999900001",  # Non-matching SIRET
        bsda_data_df=bsda_data,
        bsda_transporters_data_df=transporters_data,
        data_date_interval=date_interval,
    )
    empty_processor._preprocess_bs_data()
    assert empty_processor._check_data_empty()  # Data should be empty


def test_create_figure(bsda_data, transporters_data, date_interval):
    """Test figure creation."""
    processor = BsdaWorkerQuantityProcessor(
        company_siret="12345678900001",
        bsda_data_df=bsda_data,
        bsda_transporters_data_df=transporters_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_bs_data()
    processor._create_figure()

    assert processor.figure is not None
    assert isinstance(processor.figure, Figure)  # Check if it's a Plotly Figure


def test_build(bsda_data, transporters_data, date_interval):
    """Test build method."""
    processor = BsdaWorkerQuantityProcessor(
        company_siret="12345678900001",
        bsda_data_df=bsda_data,
        bsda_transporters_data_df=transporters_data,
        data_date_interval=date_interval,
    )
    result = processor.build()

    assert result is not None
    assert isinstance(result, str)  # Build returns the JSON of the figure
    assert "data" in result  # Check if "data" key exists in JSON
