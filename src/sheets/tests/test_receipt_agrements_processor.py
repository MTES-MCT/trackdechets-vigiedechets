from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from ..graph_processors.html_components import ReceiptAgrementsProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_receipts_agreements_data():
    now = datetime.now(tz=tz)
    return {
        "Récépissé transporteur": pl.LazyFrame(
            {
                "id": ["receipt-1"],
                "receipt_number": ["T-12345"],
                "validity_limit": [now + timedelta(days=30)],
            }
        ),
        "Agrément VHU": pl.LazyFrame(
            {
                "id": ["agrement-1"],
                "receipt_number": ["VHU-9876"],
            }
        ),
    }


def test_receipt_agrements_processor_returns_formatted_receipts(sample_receipts_agreements_data):
    """
    GIVEN: Company with valid and invalid receipts/agreements.
    WHEN: Building receipt/agreement context.
    THEN: Returns list with receipt names, numbers, and validity strings.
    """
    processor = ReceiptAgrementsProcessor(
        receipts_agreements_data=sample_receipts_agreements_data,
    )

    result = processor.build()

    assert isinstance(result, list)
    assert len(result) == 2

    # Check receipt with validity date
    receipt_transporteur = [r for r in result if r["name"] == "Récépissé transporteur"][0]
    assert receipt_transporteur["number"] == "T-12345"
    assert "valide jusqu'au" in receipt_transporteur["validity_str"]

    # Check agrément without validity date
    agrement_vhu = [r for r in result if r["name"] == "Agrément VHU"][0]
    assert agrement_vhu["number"] == "VHU-9876"
    assert agrement_vhu["validity_str"] == ""


def test_receipt_agrements_processor_marks_expired_receipts():
    """
    GIVEN: Receipt with validity_limit in the past.
    WHEN: Building receipt/agreement context.
    THEN: Marks receipt as expired in validity_str.
    """
    now = datetime.now(tz=tz)
    receipts_data = {
        "Récépissé transporteur": pl.LazyFrame(
            {
                "id": ["receipt-1"],
                "receipt_number": ["T-EXPIRED"],
                "validity_limit": [now - timedelta(days=10)],
            }
        ),
    }

    processor = ReceiptAgrementsProcessor(
        receipts_agreements_data=receipts_data,
    )

    result = processor.build()

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["number"] == "T-EXPIRED"
    assert "expiré depuis le" in result[0]["validity_str"]


def test_receipt_agrements_processor_returns_empty_when_no_data():
    """
    GIVEN: No receipts/agreements data.
    WHEN: Building receipt/agreement context.
    THEN: Returns empty list.
    """
    processor = ReceiptAgrementsProcessor(
        receipts_agreements_data={},
    )

    result = processor.build()

    assert result == []
