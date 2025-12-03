from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from sheets.constants import BSDD, BSFF

from ..graph_processors.plotly_components import BsdQuantitiesGraph

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_data_bsdd():
    data = {
        "id": [1, 2, 3, 4],
        "recipient_company_siret": ["12345678900011", "12345678900011", "98765432100022", "12345678900011"],
        "emitter_company_siret": ["98765432100022", "98765432100022", "12345678900011", "98765432100011"],
        "received_at": [
            datetime(2024, 1, 10, tzinfo=tz),
            datetime(2024, 2, 15, tzinfo=tz),
            datetime(2024, 3, 20, tzinfo=tz),
            datetime(2024, 4, 25, tzinfo=tz),
        ],
        "sent_at": [
            datetime(2024, 1, 5, tzinfo=tz),
            datetime(2024, 2, 10, tzinfo=tz),
            datetime(2024, 3, 15, tzinfo=tz),
            datetime(2024, 4, 20, tzinfo=tz),
        ],
        "quantity_received": [10, 20, 30, 40],
        "quantity_refused": [1, None, 2, 40],
    }
    return pl.DataFrame(data).lazy()


@pytest.fixture
def sample_data_bsff():
    data = {
        "id": [1, 2, 3, 4],
        "recipient_company_siret": ["12345678900011", "98765432100022", "98765432100022", "12345678900011"],
        "emitter_company_siret": ["98765432100022", "12345678900011", "12345678900011", "98765432100011"],
        "sent_at": [
            datetime(2024, 1, 5, tzinfo=tz),
            datetime(2024, 2, 10, tzinfo=tz),
            datetime(2024, 3, 15, tzinfo=tz),
            datetime(2024, 4, 20, tzinfo=tz),
        ],
        "received_at": [
            datetime(2024, 1, 10, tzinfo=tz),
            datetime(2024, 2, 15, tzinfo=tz),
            datetime(2024, 3, 20, tzinfo=tz),
            datetime(2024, 4, 25, tzinfo=tz),
        ],
    }
    return pl.DataFrame(data).lazy()


@pytest.fixture
def sample_packagings():
    data = {
        "bsff_id": [1, 2, 2, 4, 4],
        "acceptation_date": [
            datetime(2024, 1, 12, tzinfo=tz),
            datetime(2024, 2, 18, tzinfo=tz),
            datetime(2024, 3, 22, tzinfo=tz),
            datetime(2024, 4, 28, tzinfo=tz),
            datetime(2024, 4, 30, tzinfo=tz),
        ],
        "acceptation_weight": [5, 10, 15, 20, 3],
    }
    return pl.DataFrame(data).lazy()


def test_bsd_quantities_graph_bsdd(sample_data_bsdd):
    company_siret = "12345678900011"
    bs_type = BSDD
    data_date_interval = (
        datetime(2024, 1, 1, tzinfo=tz),
        datetime(2024, 12, 31, tzinfo=tz),
    )
    quantity_variables_names = ["quantity_received"]

    processor = BsdQuantitiesGraph(
        company_siret=company_siret,
        bs_type=bs_type,
        bs_data=sample_data_bsdd,
        data_date_interval=data_date_interval,
        quantity_variables_names=quantity_variables_names,
    )

    processor._preprocess_data()

    expected_incoming_data_by_month_series = pl.DataFrame(
        {
            "received_at": [
                datetime(2024, 1, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2024, 2, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2024, 4, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
            ],
            "quantity_received": [9, 20, 0],
        }
    )
    expected_outgoing_data_by_month_series = pl.DataFrame(
        {
            "sent_at": [datetime(2024, 3, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris"))],
            "quantity_received": [28],
        }
    )

    assert_frame_equal(processor.incoming_data_by_month_series[0], expected_incoming_data_by_month_series)
    assert_frame_equal(processor.outgoing_data_by_month_series[0], expected_outgoing_data_by_month_series)


def test_empty_data(sample_data_bsdd):
    company_siret = "12345678900011"
    bs_type = BSDD
    quantity_variables_names = ["quantity_received"]

    # First case: no data in the interval
    data_date_interval = (
        datetime(2025, 1, 1, tzinfo=tz),
        datetime(2025, 12, 31, tzinfo=tz),
    )
    processor = BsdQuantitiesGraph(
        company_siret=company_siret,
        bs_type=bs_type,
        bs_data=sample_data_bsdd,
        data_date_interval=data_date_interval,
        quantity_variables_names=quantity_variables_names,
    )
    processor._preprocess_data()
    assert processor._check_data_empty() is True

    # Second case: all NaNs
    empty_df = (
        sample_data_bsdd.collect()
        .with_columns(
            [
                pl.lit(None).alias("quantity_received").cast(pl.Float64),
                pl.lit(None).alias("quantity_refused").cast(pl.Float64),
            ]
        )
        .lazy()
    )

    data_date_interval = (
        datetime(2024, 1, 1, tzinfo=tz),
        datetime(2024, 12, 31, tzinfo=tz),
    )
    processor = BsdQuantitiesGraph(
        company_siret=company_siret,
        bs_type=bs_type,
        bs_data=empty_df,
        data_date_interval=data_date_interval,
        quantity_variables_names=quantity_variables_names,
    )
    processor._preprocess_data()


def test_bsd_quantities_graph_bsff(sample_data_bsff, sample_packagings):
    company_siret = "12345678900011"
    bs_type = BSFF
    data_date_interval = (
        datetime(2024, 1, 1, tzinfo=tz),
        datetime(2024, 12, 31, tzinfo=tz),
    )
    quantity_variables_names = ["acceptation_weight"]

    processor = BsdQuantitiesGraph(
        company_siret=company_siret,
        bs_type=bs_type,
        bs_data=sample_data_bsff,
        data_date_interval=data_date_interval,
        quantity_variables_names=quantity_variables_names,
        packagings_data=sample_packagings,
    )
    processor._preprocess_data()

    expected_incoming_data_by_month_series = pl.DataFrame(
        {
            "received_at": [
                datetime(2024, 1, 1, tzinfo=tz),
                datetime(2024, 4, 1, tzinfo=tz),
            ],
            "acceptation_weight": [5.0, 23.0],
        },
    )

    expected_outgoing_data_by_month_series = pl.DataFrame(
        {
            "sent_at": [datetime(2024, 2, 1, tzinfo=tz)],
            "acceptation_weight": [25.0],
        },
    )

    assert_frame_equal(processor.incoming_data_by_month_series[0], expected_incoming_data_by_month_series)
    assert_frame_equal(processor.outgoing_data_by_month_series[0], expected_outgoing_data_by_month_series)


def test_bsd_quantities_graph_bsff_without_acceptation_date(sample_data_bsff, sample_packagings):
    company_siret = "12345678900011"
    bs_type = BSFF
    data_date_interval = (
        datetime(2024, 1, 1, tzinfo=tz),
        datetime(2024, 12, 31, tzinfo=tz),
    )
    quantity_variables_names = ["acceptation_weight"]

    # Remove acceptation_date
    empty_packagings = (
        sample_packagings.collect()
        .with_columns(pl.lit(None).cast(pl.Datetime(time_zone="Europe/Paris")).alias("acceptation_date"))
        .lazy()
    )

    processor = BsdQuantitiesGraph(
        company_siret=company_siret,
        bs_type=bs_type,
        bs_data=sample_data_bsff,
        data_date_interval=data_date_interval,
        quantity_variables_names=quantity_variables_names,
        packagings_data=empty_packagings,
    )

    processor._preprocess_data()

    expected_incoming_data_by_month_series = pl.DataFrame(
        {"received_at": [], "acceptation_weight": []},
        schema_overrides={
            "received_at": pl.Datetime(time_unit="us", time_zone="Europe/Paris"),
            "acceptation_weight": pl.Float64,
        },
    )

    expected_outgoing_data_by_month_series = pl.DataFrame(
        {"sent_at": [datetime(2024, 2, 1, tzinfo=tz)], "acceptation_weight": [25.0]},
    )

    assert_frame_equal(processor.incoming_data_by_month_series[0], expected_incoming_data_by_month_series)
    assert_frame_equal(processor.outgoing_data_by_month_series[0], expected_outgoing_data_by_month_series)
