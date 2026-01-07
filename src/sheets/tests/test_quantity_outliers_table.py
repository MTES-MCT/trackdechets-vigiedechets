from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from sheets.constants import BSDD, BSFF

from ..graph_processors.html_components import QuantityOutliersTableProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def bs_data_dfs():
    return {
        BSDD: pl.LazyFrame(
            {
                "id": [1, 2, 3, 4],
                "readable_id": [1, 2, 3, 4],
                "quantity_received": [50.0, 10.0, 45.0, 5.0],
                "quantity_refused": [7.0, None, None, 2.0],
                "received_at": [
                    datetime(2024, 8, 12, tzinfo=tz),
                    datetime(2024, 8, 13, tzinfo=tz),
                    datetime(2024, 8, 14, tzinfo=tz),
                    datetime(2024, 8, 15, tzinfo=tz),
                ],
                "emitter_company_siret": ["12345678900011", "12345678900011", "98765432100022", "98765432100022"],
                "recipient_company_siret": ["98765432100022", "98765432100022", "100000000000000", "12345678900011"],
                "waste_code": ["01 01 01*"] * 4,
                "waste_name": ["Waste Type A"] * 4,
            }
        ),
        BSFF: pl.LazyFrame(
            {
                "id": [5, 6, 7, 8],
                "sent_at": [
                    datetime(2024, 8, 10, tzinfo=tz),
                    datetime(2024, 8, 11, tzinfo=tz),
                    datetime(2024, 8, 12, tzinfo=tz),
                    datetime(2024, 8, 13, tzinfo=tz),
                ],
                "received_at": [
                    datetime(2024, 8, 12, tzinfo=tz),
                    datetime(2024, 8, 13, tzinfo=tz),
                    datetime(2024, 8, 14, tzinfo=tz),
                    datetime(2024, 8, 15, tzinfo=tz),
                ],
                "emitter_company_siret": ["12345678900011", "12345678900011", "98765432100022", "98765432100022"],
                "recipient_company_siret": ["98765432100022", "98765432100022", "100000000000000", "12345678900011"],
                "waste_code": ["01 02 01*"] * 4,
                "waste_name": ["Waste Type A"] * 4,
            }
        ),
    }


@pytest.fixture
def packagings_data_df():
    return pl.LazyFrame(
        {
            "bsff_id": [5, 5, 6, 7, 8],
            "acceptation_weight": [3.0, 40.0, 1.0, 2.4, 5.0],
            "acceptation_date": [
                datetime(2024, 8, 12, tzinfo=tz),
                datetime(2024, 8, 12, tzinfo=tz),
                datetime(2024, 8, 13, tzinfo=tz),
                datetime(2024, 8, 14, tzinfo=tz),
                datetime(2024, 8, 15, tzinfo=tz),
            ],
        }
    )


@pytest.fixture
def transporters_data_df():
    return {
        BSDD: pl.LazyFrame(
            {
                "bs_id": [1, 2, 3, 4],
                "transporter_company_siret": [
                    "100000000000000",
                    "100000000000000",
                    "12345678900011",
                    "100000000000000",
                ],
                "transporter_transport_mode": ["ROAD", "ROAD", "ROAD", "ROAD"],
                "sent_at": [
                    datetime(2024, 8, 10, tzinfo=tz),
                    datetime(2024, 8, 11, tzinfo=tz),
                    datetime(2024, 8, 12, tzinfo=tz),
                    datetime(2024, 8, 13, tzinfo=tz),
                ],
            }
        ),
        BSFF: pl.LazyFrame(
            {
                "bs_id": [5, 6, 7, 8],
                "transporter_company_siret": [
                    "100000000000000",
                    "100000000000000",
                    "12345678900011",
                    "100000000000000",
                ],
                "transporter_transport_mode": ["ROAD", "ROAD", "ROAD", "ROAD"],
                "sent_at": [
                    datetime(2024, 8, 10, tzinfo=tz),
                    datetime(2024, 8, 11, tzinfo=tz),
                    datetime(2024, 8, 12, tzinfo=tz),
                    datetime(2024, 8, 13, tzinfo=tz),
                ],
            }
        ),
    }


@pytest.fixture
def data_date_interval():
    return datetime(2024, 8, 1, tzinfo=tz), datetime(2024, 9, 30, tzinfo=tz)


def test_preprocess_data(bs_data_dfs, transporters_data_df, packagings_data_df, data_date_interval):
    """
    GIVEN: BSDD and BSFF with outlier quantities (>40t for road transport).
    WHEN: Preprocessing quantity outliers.
    THEN: Returns only bordereaux exceeding threshold with formatted dates.
    """
    processor = QuantityOutliersTableProcessor(
        bs_data_dfs=bs_data_dfs,
        transporters_data_df=transporters_data_df,
        data_date_interval=data_date_interval,
        packagings_data_df=packagings_data_df,
    )
    processor._preprocess_data()
    preprocessed_data = processor.preprocessed_data

    expected_data = pl.DataFrame(
        {
            "id": [1, 3, 5],
            "readable_id": [1, 3, None],
            "quantity_received": [50.0, 45.0, 43.0],
            "quantity_refused": [7.0, None, None],
            "received_at": ["12/08/2024 00:00", "14/08/2024 00:00", "12/08/2024 00:00"],
            "emitter_company_siret": ["12345678900011", "98765432100022", "12345678900011"],
            "recipient_company_siret": ["98765432100022", "100000000000000", "98765432100022"],
            "waste_code": ["01 01 01*", "01 01 01*", "01 02 01*"],
            "waste_name": ["Waste Type A", "Waste Type A", "Waste Type A"],
            "transporter_company_siret": ["100000000000000", "12345678900011", "100000000000000"],
            "transporter_transport_mode": ["ROAD", "ROAD", "ROAD"],
            "sent_at": ["10/08/2024 00:00", "12/08/2024 00:00", "10/08/2024 00:00"],
            "bs_type": ["bsdd", "bsdd", "bsff"],
        },
    )
    assert_frame_equal(preprocessed_data, expected_data)


def test_check_data_empty(bs_data_dfs, transporters_data_df, packagings_data_df):
    """
    GIVEN: Date interval with no bordereaux sent.
    WHEN: Checking if outliers data is empty.
    THEN: Returns True (no outliers).
    """
    processor = QuantityOutliersTableProcessor(
        bs_data_dfs=bs_data_dfs,
        transporters_data_df=transporters_data_df,
        data_date_interval=(datetime(2024, 9, 10, tzinfo=tz), datetime(2024, 10, 10, tzinfo=tz)),
        packagings_data_df=packagings_data_df,
    )
    assert processor._check_data_empty() is True


def test_build(bs_data_dfs, transporters_data_df, data_date_interval, packagings_data_df):
    """
    GIVEN: BSDD and BSFF with outlier quantities.
    WHEN: Building final outliers list with formatted quantities.
    THEN: Returns list of outlier records with all expected fields.
    """
    processor = QuantityOutliersTableProcessor(
        bs_data_dfs=bs_data_dfs,
        transporters_data_df=transporters_data_df,
        data_date_interval=data_date_interval,
        packagings_data_df=packagings_data_df,
    )
    results = processor.build()

    expected_data = [
        {
            "id": 1,
            "bs_type": "bsdd",
            "emitter_company_siret": "12345678900011",
            "transporter_company_siret": "100000000000000",
            "recipient_company_siret": "98765432100022",
            "waste_code": "01 01 01*",
            "waste_name": "Waste Type A",
            "quantity": "50",
            "quantity_refused": "7",
            "sent_at": "10/08/2024 00:00",
            "received_at": "12/08/2024 00:00",
        },
        {
            "id": 3,
            "bs_type": "bsdd",
            "emitter_company_siret": "98765432100022",
            "transporter_company_siret": "12345678900011",
            "recipient_company_siret": "100000000000000",
            "waste_code": "01 01 01*",
            "waste_name": "Waste Type A",
            "quantity": "45",
            "quantity_refused": "0",
            "sent_at": "12/08/2024 00:00",
            "received_at": "14/08/2024 00:00",
        },
        {
            "id": 5,
            "bs_type": "bsff",
            "emitter_company_siret": "12345678900011",
            "transporter_company_siret": "100000000000000",
            "recipient_company_siret": "98765432100022",
            "waste_code": "01 02 01*",
            "waste_name": "Waste Type A",
            "quantity": "43",
            "quantity_refused": "0",
            "sent_at": "10/08/2024 00:00",
            "received_at": "12/08/2024 00:00",
        },
    ]

    assert results == expected_data
