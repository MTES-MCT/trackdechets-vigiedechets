from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from ..graph_processors.html_components import RegistryStatsProcessor

tz = ZoneInfo("Europe/Paris")


# Sample fixture for test data
@pytest.fixture
def rndts_test_data():
    incoming_data = pl.LazyFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "reception_date": [
                datetime(2024, 8, 9, tzinfo=tz),
                datetime(2024, 8, 10, tzinfo=tz),
                datetime(2024, 7, 15, tzinfo=tz),  # Outside date interval
                datetime(2024, 8, 11, tzinfo=tz),
                datetime(2024, 9, 12, tzinfo=tz),
            ],
            "siret": [
                "12345678901234",
                "12345678901234",
                "98765432109876",  # Different SIRET
                "12345678901234",
                "12345678901234",
            ],
            "weight_value": [10.0, None, 30.0, None, 50.0],
            "volume": [None, 20.0, None, 40.0, None],
        }
    )
    outgoing_data = pl.LazyFrame(
        {
            "id": [6, 7, 8, 9, 10],
            "dispatch_date": [
                datetime(2024, 8, 13, tzinfo=tz),
                datetime(2024, 8, 14, tzinfo=tz),
                datetime(2024, 10, 1, tzinfo=tz),  # Outside date interval
                datetime(2024, 8, 15, tzinfo=tz),
                datetime(2024, 8, 16, tzinfo=tz),
            ],
            "siret": [
                "12345678901234",
                "12345678901234",
                "98765432109876",  # Different SIRET
                "12345678901234",
                "12345678901234",
            ],
            "weight_value": [15.0, None, 35.0, None, 55.0],
            "volume": [None, 25.0, None, 45.0, None],
        }
    )

    date_interval = (datetime(2024, 8, 1, tzinfo=tz), datetime(2024, 9, 30, tzinfo=tz))
    company_siret = "12345678901234"

    return company_siret, incoming_data, outgoing_data, date_interval


@pytest.mark.parametrize("rndts_test_data", [False, True], indirect=True)
def test_preprocess_data(rndts_test_data):
    """Test preprocessing of incoming and outgoing data."""
    company_siret, incoming_data, outgoing_data, date_interval = rndts_test_data

    processor = RegistryStatsProcessor(company_siret, incoming_data, outgoing_data, date_interval)
    processor._preprocess_data()

    assert processor.stats["total_weight_incoming"] == 60
    assert processor.stats["total_volume_incoming"] == 60
    assert processor.stats["total_statements_incoming"] == 4

    assert processor.stats["total_weight_outgoing"] == 70
    assert processor.stats["total_volume_outgoing"] == 70
    assert processor.stats["total_statements_outgoing"] == 4


@pytest.mark.parametrize("rndts_test_data", [False, True], indirect=True)
def test_empty_data_handling(rndts_test_data):
    """Test handling of empty dataframes."""
    company_siret, incoming_data, outgoing_data, date_interval = rndts_test_data

    processor = RegistryStatsProcessor(company_siret, incoming_data.head(0), outgoing_data.head(0), date_interval)
    processor._preprocess_data()

    assert processor._check_data_empty()

    # Case empty data due to date interval miss
    processor = RegistryStatsProcessor(
        company_siret,
        incoming_data.head(0),
        outgoing_data.head(0),
        tuple(e - timedelta(days=365) for e in date_interval),
    )
    processor._preprocess_data()

    assert processor._check_data_empty()


@pytest.mark.parametrize("rndts_test_data", [False, True], indirect=True)
def test_bar_size_calculation(rndts_test_data):
    """Test bar size calculation for incoming and outgoing data."""
    company_siret, incoming_data, outgoing_data, date_interval = rndts_test_data

    processor = RegistryStatsProcessor(company_siret, incoming_data, outgoing_data, date_interval)
    processor._preprocess_data()

    assert processor.stats["bar_size_weight_incoming"] == 85  # Relative size
    assert processor.stats["bar_size_weight_outgoing"] == 100

    assert processor.stats["bar_size_volume_incoming"] == 85  # Relative size
    assert processor.stats["bar_size_volume_outgoing"] == 100


@pytest.mark.parametrize("rndts_test_data", [False, True], indirect=True)
def test_context_building(rndts_test_data):
    """Test that context is correctly built and formatted."""
    company_siret, incoming_data, outgoing_data, date_interval = rndts_test_data

    processor = RegistryStatsProcessor(company_siret, incoming_data, outgoing_data, date_interval)
    processor._preprocess_data()
    context = processor.build_context()

    assert context["total_weight_incoming"] == "60"
    assert context["total_weight_outgoing"] == "70"
    assert context["total_statements_incoming"] == "4"
    assert context["total_statements_outgoing"] == "4"


@pytest.mark.parametrize("rndts_test_data", [False, True], indirect=True)
def test_full_build(rndts_test_data):
    """Test the full build method."""
    company_siret, incoming_data, outgoing_data, date_interval = rndts_test_data

    processor = RegistryStatsProcessor(company_siret, incoming_data, outgoing_data, date_interval)
    data = processor.build()

    expected_data = {
        "total_weight_incoming": "60",
        "total_weight_outgoing": "70",
        "bar_size_weight_incoming": "85",
        "bar_size_weight_outgoing": "100",
        "has_weight": True,
        "total_volume_incoming": "60",
        "total_volume_outgoing": "70",
        "bar_size_volume_incoming": "85",
        "bar_size_volume_outgoing": "100",
        "has_volume": True,
        "total_statements_incoming": "4",
        "total_statements_outgoing": "4",
    }
    assert data == expected_data
