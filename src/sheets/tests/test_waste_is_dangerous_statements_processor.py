from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from ..graph_processors.html_components import WasteIsDangerousStatementsProcessor

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
            "emitter_company_siret": ["12345678900011", "12345678900011", "98765432100022", "12345678900011"],
            "is_dangerous": [True, True, False, True],
            "waste_code": ["20 01 02", "20 01 02", "20 01 03*", "20 01 04*"],  # Non-* codes with is_dangerous=True
            "quantity_received": [100.0, 50.0, 30.0, 20.0],
            "quantity_refused": [0.0, 10.0, 0.0, 5.0],
        }
    )


@pytest.fixture
def sample_bsdd_transporters_data():
    return pl.LazyFrame(
        {
            "bs_id": ["bsdd-1", "bsdd-2", "bsdd-3", "bsdd-4"],
            "sent_at": [
                datetime(2024, 1, 10, tzinfo=tz),
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 1, 20, tzinfo=tz),
                datetime(2024, 1, 25, tzinfo=tz),
            ],
            "transporter_company_siret": ["98765432100022", "98765432100022", "98765432100022", "98765432100022"],
        }
    )


def test_waste_is_dangerous_statements_processor_filters_correctly(
    sample_bsdd_data, sample_bsdd_transporters_data, sample_waste_codes
):
    """
    GIVEN: Company with is_dangerous=True waste but non-dangerous waste codes (no *).
    WHEN: Building waste-is-dangerous statements.
    THEN: Returns list of waste codes filtered for is_dangerous=True, non-* codes, emitter=company.
    """
    processor = WasteIsDangerousStatementsProcessor(
        company_siret="12345678900011",
        bsdd_data=sample_bsdd_data,
        bsdd_transporters_data=sample_bsdd_transporters_data,
        waste_codes_df=sample_waste_codes,
        data_date_interval=(datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 1, 31, tzinfo=tz)),
    )

    result = processor.build()

    assert isinstance(result, list)
    # Only bsdd-1 and bsdd-2 qualify: is_dangerous=True, waste_code="20 01 02" (no *), emitter=12345678900011
    assert len(result) >= 1

    waste_codes_in_result = [item["waste_code"] for item in result]
    assert "20 01 02" in waste_codes_in_result

    # Check aggregation: bsdd-1: 100-0=100, bsdd-2: 50-10=40 => total=140, count=2
    item_20_01_02 = [item for item in result if item["waste_code"] == "20 01 02"][0]
    assert item_20_01_02["count"] == 2
    assert item_20_01_02["quantity"] == "140"


def test_waste_is_dangerous_statements_processor_returns_empty_when_no_match():
    """
    GIVEN: Company with only dangerous waste codes (with *) or not marked is_dangerous.
    WHEN: Building waste-is-dangerous statements.
    THEN: Returns empty list.
    """
    bsdd_data = pl.LazyFrame(
        {
            "id": ["bsdd-1"],
            "emitter_company_siret": ["12345678900011"],
            "is_dangerous": [False],
            "waste_code": ["20 01 02"],
            "quantity_received": [50.0],
            "quantity_refused": [0.0],
        }
    )

    bsdd_transporters_data = pl.LazyFrame(
        {
            "bs_id": ["bsdd-1"],
            "sent_at": [datetime(2024, 1, 10, tzinfo=tz)],
            "transporter_company_siret": ["98765432100022"],
        }
    )

    waste_codes = pl.LazyFrame(
        {
            "code": ["20 01 02"],
            "description": ["Test waste"],
        }
    )

    processor = WasteIsDangerousStatementsProcessor(
        company_siret="12345678900011",
        bsdd_data=bsdd_data,
        bsdd_transporters_data=bsdd_transporters_data,
        waste_codes_df=waste_codes,
        data_date_interval=(datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 1, 31, tzinfo=tz)),
    )

    result = processor.build()

    assert result == []
