from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from ..graph_processors.html_components import TraceabilityInterruptionsProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_waste_codes():
    current_dir = Path(__file__).parent.parent.parent
    return pl.read_csv(
        Path(current_dir, "csv", "code_dechets.csv"), schema_overrides={"code": pl.String, "description": pl.String}
    ).lazy()


@pytest.fixture
def sample_bsdd_data():
    return pl.LazyFrame(
        {
            "id": ["bsdd-1", "bsdd-2", "bsdd-3", "bsdd-4"],
            "recipient_company_siret": ["12345678900011", "12345678900011", "98765432100022", "12345678900011"],
            "no_traceability": [True, True, True, False],
            "waste_code": ["20 01 01*", "20 01 01*", "20 01 02", "20 01 03*"],
            "quantity_received": [100.0, 50.0, 30.0, 20.0],
            "quantity_refused": [0.0, 10.0, 0.0, 5.0],
            "received_at": [
                datetime(2024, 1, 10, tzinfo=tz),
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 1, 20, tzinfo=tz),
                datetime(2024, 1, 25, tzinfo=tz),
            ],
        }
    )


def test_traceability_interruptions_processor_aggregates_by_waste_code(sample_bsdd_data, sample_waste_codes):
    """
    GIVEN: Company with BSDs marked as traceability interruptions.
    WHEN: Building traceability interruptions stats.
    THEN: Returns list of waste codes with aggregated quantity and count, sorted descending.
    """
    processor = TraceabilityInterruptionsProcessor(
        company_siret="12345678900011",
        bsdd_data=sample_bsdd_data,
        waste_codes_df=sample_waste_codes,
        data_date_interval=(datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 1, 31, tzinfo=tz)),
    )

    result = processor.build()

    assert isinstance(result, list)
    assert len(result) >= 1

    # Check that only no_traceability=True and recipient=company_siret are included
    # bsdd-1: 100-0=100, bsdd-2: 50-10=40 => total for "20 01 01*" = 140, count=2
    waste_codes_in_result = [item["waste_code"] for item in result]
    assert "20 01 01*" in waste_codes_in_result

    item_20_01_01 = [item for item in result if item["waste_code"] == "20 01 01*"][0]
    assert item_20_01_01["count"] == 2
    assert item_20_01_01["quantity"] == "140"


def test_traceability_interruptions_processor_returns_empty_when_no_interruptions():
    """
    GIVEN: Company with no traceability interruptions (all no_traceability=False).
    WHEN: Building traceability interruptions stats.
    THEN: Returns empty list.
    """
    bsdd_data = pl.LazyFrame(
        {
            "id": ["bsdd-1"],
            "recipient_company_siret": ["12345678900011"],
            "no_traceability": [False],
            "waste_code": ["20 01 01*"],
            "quantity_received": [50.0],
            "quantity_refused": [0.0],
            "received_at": [datetime(2024, 1, 10, tzinfo=tz)],
        }
    )

    waste_codes = pl.LazyFrame(
        {
            "code": ["20 01 01*"],
            "description": ["Test waste"],
        }
    )

    processor = TraceabilityInterruptionsProcessor(
        company_siret="12345678900011",
        bsdd_data=bsdd_data,
        waste_codes_df=waste_codes,
        data_date_interval=(datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 1, 31, tzinfo=tz)),
    )

    result = processor.build()

    assert result == []
