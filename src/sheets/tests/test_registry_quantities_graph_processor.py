from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from ..graph_processors.plotly_components import RegistryQuantitiesGraphProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_data():
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
            "weight_value": [10, None, 30, None, 50],
            "volume": [None, 20, None, 40, None],
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
            "unite": ["T", "M3", "T", "M3", "T"],
            "weight_value": [15, None, 35, None, 55],
            "volume": [None, 25, None, 45, None],
        }
    )

    date_interval = (datetime(2024, 8, 1, tzinfo=tz), datetime(2024, 9, 30, tzinfo=tz))

    return incoming_data, outgoing_data, date_interval


def test_initialization(sample_data):
    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        data_date_interval=date_interval,
    )

    assert processor.company_siret == "12345678901234"
    assert processor.registry_incoming_data is incoming_data
    assert processor.registry_outgoing_data is outgoing_data
    assert processor.data_date_interval == date_interval
    assert processor.incoming_weight_by_month_serie is None
    assert processor.outgoing_weight_by_month_serie is None
    assert processor.incoming_volume_by_month_serie is None
    assert processor.outgoing_volume_by_month_serie is None
    assert processor.figure is None


def test_preprocess_data(sample_data):
    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        data_date_interval=date_interval,
    )

    processor._preprocess_data()

    # Assert incoming data processing
    assert processor.incoming_weight_by_month_serie is not None
    assert processor.incoming_weight_by_month_serie.shape == (2, 2)
    assert processor.incoming_weight_by_month_serie["weight_value"].sum() == 60  # 10 + 50
    assert processor.incoming_volume_by_month_serie is not None
    assert processor.incoming_volume_by_month_serie["volume"].sum() == 60  # 20 + 40

    # Assert outgoing data processing
    assert processor.outgoing_weight_by_month_serie is not None
    assert processor.outgoing_weight_by_month_serie.shape == (1, 2)
    assert processor.outgoing_weight_by_month_serie["weight_value"].sum() == 70  # 15 + 55
    assert processor.outgoing_volume_by_month_serie is not None
    assert processor.outgoing_volume_by_month_serie["volume"].sum() == 70  # 25 + 45


def test_check_data_empty(sample_data):
    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        data_date_interval=date_interval,
    )

    processor._preprocess_data()

    assert not processor._check_data_empty()

    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        data_date_interval=(datetime(2023, 8, 1, tzinfo=tz), datetime(2024, 6, 30, tzinfo=tz)),
    )

    processor._preprocess_data()

    assert processor._check_data_empty()


def test_create_figure(sample_data):
    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        data_date_interval=date_interval,
    )

    processor._preprocess_data()
    processor._create_figure()

    assert processor.figure is not None


def test_build_output(sample_data):
    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        data_date_interval=date_interval,
    )

    result = processor.build()

    assert isinstance(result, str)  # JSON string
    assert len(result) > 0
