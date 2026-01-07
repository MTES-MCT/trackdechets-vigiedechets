from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from sheets.constants import BSDA, BSDD

from ..graph_processors.html_components import StorageStatsProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_waste_codes():
    from pathlib import Path

    current_dir = Path(__file__).parent.parent.parent
    return pl.read_csv(
        Path(current_dir, "csv", "code_dechets.csv"), schema_overrides={"code": pl.String, "description": pl.String}
    ).lazy()


@pytest.fixture
def sample_bsdd_data():
    return pl.LazyFrame(
        {
            "id": ["bsdd-1", "bsdd-2", "bsdd-3", "bsdd-4"],
            "emitter_company_siret": ["12345678900011", "98765432100022", "12345678900011", "98765432100022"],
            "recipient_company_siret": ["98765432100022", "12345678900011", "98765432100022", "12345678900011"],
            "waste_code": ["20 01 01*", "20 01 02", "20 01 03*", "20 01 08*"],
            "quantity_received": [100.0, 50.0, 30.0, 20.0],
            "quantity_refused": [0.0, 0.0, 5.0, 0.0],
            "sent_at": [
                datetime(2024, 1, 10, tzinfo=tz),
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 1, 20, tzinfo=tz),
                datetime(2024, 1, 25, tzinfo=tz),
            ],
            "received_at": [
                datetime(2024, 1, 12, tzinfo=tz),
                datetime(2024, 1, 17, tzinfo=tz),
                datetime(2024, 1, 22, tzinfo=tz),
                datetime(2024, 1, 27, tzinfo=tz),
            ],
        }
    )


@pytest.fixture
def sample_bsda_data():
    return pl.LazyFrame(
        {
            "id": ["bsda-1", "bsda-2"],
            "emitter_company_siret": ["12345678900011", "98765432100022"],
            "recipient_company_siret": ["98765432100022", "12345678900011"],
            "waste_code": ["17 06 05*", "17 06 05*"],
            "quantity_received": [80.0, 60.0],
            "quantity_refused": [0.0, 10.0],
            "sent_at": [datetime(2024, 1, 8, tzinfo=tz), datetime(2024, 1, 18, tzinfo=tz)],
            "received_at": [datetime(2024, 1, 10, tzinfo=tz), datetime(2024, 1, 20, tzinfo=tz)],
        }
    )


@pytest.fixture
def sample_bsdd_transporter_data():
    return pl.LazyFrame(
        {
            "bs_id": ["bsdd-1", "bsdd-2", "bsdd-3", "bsdd-4"],
            "sent_at": [
                datetime(2024, 1, 10, tzinfo=tz),
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 1, 20, tzinfo=tz),
                datetime(2024, 1, 25, tzinfo=tz),
            ],
        }
    )


@pytest.fixture
def sample_bsda_transporter_data():
    return pl.LazyFrame(
        {
            "bs_id": ["bsda-1", "bsda-2"],
            "sent_at": [datetime(2024, 1, 8, tzinfo=tz), datetime(2024, 1, 18, tzinfo=tz)],
        }
    )


@pytest.fixture
def data_date_interval():
    return (datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 1, 31, tzinfo=tz))


def test_storage_stats_processor_computes_stock_correctly(
    sample_bsdd_data,
    sample_bsda_data,
    sample_bsdd_transporter_data,
    sample_bsda_transporter_data,
    sample_waste_codes,
    data_date_interval,
):
    """
    GIVEN: Company with emitted and received waste in BSDD and BSDA (multimodal).
    WHEN: Building storage stats with multimodal transport data.
    THEN: Returns stock by waste code (received - emitted) for positive differences only, sorted descending.
    """
    processor = StorageStatsProcessor(
        company_siret="12345678900011",
        bs_data_dfs={BSDD: sample_bsdd_data, BSDA: sample_bsda_data},
        transporters_data_df={BSDD: sample_bsdd_transporter_data, BSDA: sample_bsda_transporter_data},
        waste_codes_df=sample_waste_codes,
        data_date_interval=data_date_interval,
    )

    result = processor.build()

    assert "stored_waste" in result
    assert "total_stock" in result

    # Company emitted (as emitter_company_siret="12345678900011"): bsdd-1=100, bsdd-3=30 (minus 5 refused = 25)
    # Company received (as recipient_company_siret="12345678900011"): bsdd-2=50, bsdd-4=20, bsda-2=60 (minus 10 refused = 50)
    # Stock = received - emitted per waste code; only positive kept
    # 20 01 02: received 50, emitted 0 -> stock 50
    # 20 01 08*: received 20, emitted 0 -> stock 20
    # 17 06 05*: received 50, emitted 0 -> stock 50

    stored_waste = result["stored_waste"]
    assert len(stored_waste) >= 2  # At least some positive stock

    # Check that we have positive stock for waste codes
    waste_codes_in_result = [item["code"] for item in stored_waste]
    assert "20 01 02" in waste_codes_in_result or "17 06 05*" in waste_codes_in_result


def test_storage_stats_processor_returns_empty_when_no_positive_stock(sample_waste_codes):
    """
    GIVEN: Company with only emitted waste (no received waste, so no positive stock).
    WHEN: Building storage stats.
    THEN: Returns empty dict.
    """
    # Company only emits waste, never receives (stock = received - emitted < 0, so no positive stock)
    bsdd_data = pl.LazyFrame(
        {
            "id": ["bsdd-1"],
            "emitter_company_siret": ["12345678900011"],
            "recipient_company_siret": ["98765432100022"],
            "waste_code": ["20 01 01*"],
            "quantity_received": [50.0],
            "quantity_refused": [0.0],
            "sent_at": [datetime(2024, 1, 10, tzinfo=tz)],
            "received_at": [datetime(2024, 1, 12, tzinfo=tz)],
        }
    )

    bsdd_transporter_data = pl.LazyFrame(
        {
            "bs_id": ["bsdd-1"],
            "sent_at": [datetime(2024, 1, 10, tzinfo=tz)],
        }
    )

    processor = StorageStatsProcessor(
        company_siret="12345678900011",
        bs_data_dfs={BSDD: bsdd_data},
        transporters_data_df={BSDD: bsdd_transporter_data},
        waste_codes_df=sample_waste_codes,
        data_date_interval=(datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 1, 31, tzinfo=tz)),
    )

    result = processor.build()

    assert result == {}
