from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from sheets.constants import BSDD

from ..graph_processors.html_components_processors import BsdStatsProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_bs_data():
    # Create a sample DataFrame for bs_data
    created_at_datetimes = [
        datetime(2024, 11, 1, tzinfo=tz),
        datetime(2024, 11, 4, tzinfo=tz),
        datetime(2024, 11, 9, tzinfo=tz),
        datetime(2024, 12, 1, tzinfo=tz),
        datetime(2024, 12, 18, tzinfo=tz),
        datetime(2024, 12, 31, tzinfo=tz),
    ]
    sent_at_datetimes = [e + timedelta(days=1) for e in created_at_datetimes]
    received_at_datetimes = [e + timedelta(days=1) for e in sent_at_datetimes]
    time_to_process = [60, 1, 1, 1, 60, 1]
    processed_at_datetimes = [e + timedelta(days=t) for e, t in zip(received_at_datetimes, time_to_process)]

    bs_data = pl.DataFrame(
        {
            "id": [i for i in range(1, 7)],
            "emitter_company_siret": ["123456789", "987654321", "123456789", "123456789", "987654321", "987654321"],
            "recipient_company_siret": ["987654321", "123456789", "987654321", "987654321", "123456789", "123456789"],
            "created_at": created_at_datetimes,
            "sent_at": sent_at_datetimes,
            "received_at": received_at_datetimes,
            "processed_at": processed_at_datetimes,
            "status": ["PROCESSED", "REFUSED", "RECEIVED", "SENT", "PROCESSED", "PROCESSED"],
            "quantity_received": [10.0, 20.0, 2.5, 5, 8, 6.7],
            "quantity_refused": [1.0, None, 2.5, 0.0, None, 1.3],
            "volume": [10.0, 20.0, 2.5, 5, 8, 6.7],
        }
    )
    return bs_data.lazy()


@pytest.fixture
def sample_bs_data_empty():
    # Create a sample DataFrame for bs_data that should generate empty component
    now = datetime.now(tz=tz)
    bs_data = pl.DataFrame(
        {
            "id": [1, 2],
            "emitter_company_siret": ["123456789", "987654321"],
            "recipient_company_siret": ["987654321", "123456789"],
            "created_at": [now - timedelta(days=3000), now - timedelta(days=65)],
            "sent_at": [now - timedelta(days=2900), now - timedelta(days=40)],
            "received_at": [now - timedelta(days=2900), None],
            "processed_at": [now - timedelta(days=2000), None],
            "status": ["PROCESSED", "SENT"],
            "quantity_received": [10.0, None],
            "quantity_refused": [2.0, None],
        }
    )
    return bs_data.lazy()


@pytest.fixture
def data_date_interval():
    return datetime(2024, 11, 1, tzinfo=tz), datetime(2024, 12, 26, tzinfo=tz)


@pytest.mark.parametrize(
    "siret, expected",
    [
        (
            "123456789",
            {
                "emitted_bs_stats": {
                    "total": "3",
                    "archived": "1",
                    "avg_processing_time": "20.7j",
                    "processed_in_more_than_one_month_count": "1",
                    "processed_in_more_than_one_month_avg_processing_time": "60j",
                },
                "received_bs_stats": {
                    "total": "2",
                    "archived": "2",
                    "avg_processing_time": "30.5j",
                    "processed_in_more_than_one_month_count": "1",
                    "processed_in_more_than_one_month_avg_processing_time": "60j",
                },
                "quantities_stats": {
                    "quantity_received": {
                        "total_quantity_incoming": "28",
                        "total_quantity_outgoing": "14",
                        "bar_size_incoming": 100,
                        "bar_size_outgoing": 50,
                    }
                },
                "revised_bs_count": "0",
                "pending_revisions_count": "0",
                "weight_volume_ratio": None,
            },
        ),
        (
            "987654321",
            {
                "emitted_bs_stats": {
                    "total": "2",
                    "archived": "2",
                    "avg_processing_time": "30.5j",
                    "processed_in_more_than_one_month_count": "1",
                    "processed_in_more_than_one_month_avg_processing_time": "60j",
                },
                "received_bs_stats": {
                    "total": "3",
                    "archived": "1",
                    "avg_processing_time": "20.7j",
                    "processed_in_more_than_one_month_count": "1",
                    "processed_in_more_than_one_month_avg_processing_time": "60j",
                },
                "quantities_stats": {
                    "quantity_received": {
                        "total_quantity_incoming": "14",
                        "total_quantity_outgoing": "28",
                        "bar_size_incoming": 50,
                        "bar_size_outgoing": 100,
                    }
                },
                "revised_bs_count": "0",
                "pending_revisions_count": "0",
                "weight_volume_ratio": None,
            },
        ),
    ],
)
def test_bsd_stats_processor(siret, sample_bs_data, data_date_interval, expected):
    bs_processor = BsdStatsProcessor(siret, BSDD, sample_bs_data, data_date_interval)

    # Test initialization
    assert bs_processor.company_siret == siret
    assert isinstance(bs_processor.bs_data, pl.LazyFrame)
    assert bs_processor.quantity_variables_names == ["quantity_received"]
    assert bs_processor.bs_revised_data is None
    assert bs_processor.packagings_data is None

    # Test preprocessing
    bs_processor._preprocess_data()
    assert bs_processor._check_data_empty() is False

    # Test statistics computation
    context = bs_processor.build_context()

    assert context == expected


@pytest.mark.parametrize(
    "siret, quantity_variables_names, expected",
    [
        (
            "123456789",
            ["quantity_received", "volume"],
            {
                "emitted_bs_stats": {
                    "total": "3",
                    "archived": "1",
                    "avg_processing_time": "20.7j",
                    "processed_in_more_than_one_month_count": "1",
                    "processed_in_more_than_one_month_avg_processing_time": "60j",
                },
                "revised_bs_count": "0",
                "pending_revisions_count": "0",
                "received_bs_stats": {
                    "total": "2",
                    "archived": "2",
                    "avg_processing_time": "30.5j",
                    "processed_in_more_than_one_month_count": "1",
                    "processed_in_more_than_one_month_avg_processing_time": "60j",
                },
                "quantities_stats": {
                    "quantity_received": {
                        "total_quantity_incoming": "28",
                        "total_quantity_outgoing": "14",
                        "bar_size_incoming": 100,
                        "bar_size_outgoing": 50,
                    },
                    "volume": {
                        "total_quantity_incoming": "28",
                        "total_quantity_outgoing": "17.5",
                        "bar_size_incoming": 100,
                        "bar_size_outgoing": 62,
                    },
                },
                "weight_volume_ratio": "1 000",
            },
        ),
    ],
)
def test_bsd_stats_processor_multiple_quantity_variables(
    siret, quantity_variables_names, sample_bs_data, data_date_interval, expected
):
    bs_processor = BsdStatsProcessor(
        siret,
        BSDD,
        sample_bs_data,
        data_date_interval,
        quantity_variables_names=quantity_variables_names,
    )

    # Test initialization
    assert bs_processor.company_siret == siret
    assert isinstance(bs_processor.bs_data, pl.LazyFrame)
    assert set(bs_processor.quantity_variables_names) == set(quantity_variables_names)
    assert bs_processor.bs_revised_data is None
    assert bs_processor.packagings_data is None

    # Test preprocessing
    bs_processor._preprocess_data()
    assert bs_processor._check_data_empty() is False

    # Test statistics computation
    context = bs_processor.build_context()

    assert context == expected


@pytest.mark.parametrize(
    "siret, expected",
    [
        (
            "123456789",
            {},
        ),
    ],
)
def test_bsd_stats_processor_empty_data(siret, sample_bs_data_empty, data_date_interval, expected):
    # Test when the input data is empty
    bs_processor = BsdStatsProcessor(siret, BSDD, sample_bs_data_empty, data_date_interval)
    bs_processor._preprocess_data()
    assert bs_processor._check_data_empty() is True

    data = bs_processor.build()
    assert data == expected
