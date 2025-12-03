import json
from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from sheets.constants import BSDA, BSDASRI, BSDD

from ..graph_processors.html_components import IncineratorOutgoingWasteProcessor
from .constants import EXPECTED_FILES_PATH

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_data() -> dict:
    bs_data_dfs = {
        BSDD: pl.DataFrame(
            {
                "id": [1, 2, 3, 4],
                "emitter_company_siret": ["12345678901234", "12345678901234", "98765432109876", "98765432109876"],
                "recipient_company_siret": ["43210987654321", "43210987654321", "12345678901234", "87654321098769"],
                "received_at": [
                    datetime(2023, 1, 11, tzinfo=tz),
                    datetime(2023, 3, 18, tzinfo=tz),
                    datetime(2023, 5, 24, tzinfo=tz),
                    datetime(2023, 5, 21, tzinfo=tz),
                ],
                "waste_code": ["01 01 01*", "01 01 01*", "01 01 03*", "01 01 03*"],
                "waste_name": ["Déchet A", None, "Déchet B", "Déchet B"],
                "processing_operation_code": ["D10", "D10", "D5", "R1"],
                "quantity_received": [10.0, 20.0, 30.0, 19.0],
                "quantity_refused": [None, 0.0, 18.0, 5.0],
            }
        ).lazy(),
        BSDA: pl.DataFrame(
            {
                "id": [4, 5, 6, 1],
                "emitter_company_siret": ["12345678901234", "98765432109876", "12345678901234", "87654321098765"],
                "recipient_company_siret": ["87654321098765", "12345678901234", "87654321098765", "97654321098765"],
                "received_at": [
                    datetime(2023, 2, 1, tzinfo=tz),
                    datetime(2023, 4, 20, tzinfo=tz),
                    datetime(2023, 6, 10, tzinfo=tz),
                    datetime(2023, 7, 14, tzinfo=tz),
                ],
                "waste_code": ["02 01 01*", "02 01 02*", "01 01 03*", "02 01 01*"],
                "waste_name": ["Déchet C", "Déchet D", "Déchet B", "Déchet C"],
                "processing_operation_code": ["D10", "D10", "D5", "R1"],
                "quantity_received": [12.5, 32, 9.3, 10],
            }
        ).lazy(),
        BSDASRI: pl.DataFrame(
            {
                "id": [11, 22, 33, 44],
                "emitter_company_siret": ["12345678901234", "87654321098765", "98765432109876", "12345678901234"],
                "recipient_company_siret": ["43210987654321", "43210987654321", "12345678901234", "87654321098769"],
                "sent_at": [
                    datetime(2023, 1, 8, tzinfo=tz),
                    datetime(2023, 2, 18, tzinfo=tz),
                    datetime(2023, 5, 11, tzinfo=tz),
                    datetime(2023, 5, 20, tzinfo=tz),
                ],
                "received_at": [
                    datetime(2023, 1, 11, tzinfo=tz),
                    datetime(2023, 3, 18, tzinfo=tz),
                    datetime(2023, 5, 24, tzinfo=tz),
                    datetime(2023, 5, 21, tzinfo=tz),
                ],
                "waste_code": ["04 01 01*", "04 01 01*", "04 01 03*", "04 01 03*"],
                "waste_name": ["Déchet A", None, "Déchet B", "Déchet B"],
                "processing_operation_code": ["D10", "D10", "D5", "R1"],
                "quantity_received": [7.3, 0.02, 0.54, 19],
                "quantity_refused": [4.12, 0.01, 0.32, None],
            }
        ).lazy(),
    }

    transporters_data_df = {
        BSDD: pl.DataFrame(
            {
                "bs_id": [1, 2, 3, 4],
                "transporter_company_siret": ["56789012345678", "56789012345678", "97654321098765", "12345678901234"],
                "sent_at": [
                    datetime(2023, 1, 10, tzinfo=tz),
                    datetime(2023, 3, 15, tzinfo=tz),
                    datetime(2023, 5, 20, tzinfo=tz),
                    datetime(2023, 5, 20, tzinfo=tz),
                ],
                "quantity_received": [10.0, 20.0, 30.0, 19.0],
                "quantity_refused": [None, 0.0, 18.0, 5.0],
            }
        ).lazy(),
        BSDA: pl.DataFrame(
            {
                "bs_id": [4, 5, 6, 1],
                "transporter_company_siret": ["56789012345678", "56789012345678", "97654321098765", "12345678901234"],
                "sent_at": [
                    datetime(2023, 1, 10, tzinfo=tz),
                    datetime(2023, 3, 15, tzinfo=tz),
                    datetime(2023, 5, 20, tzinfo=tz),
                    datetime(2023, 5, 20, tzinfo=tz),
                ],
                "quantity_received": [12.5, 32, 9.3, 10],
            }
        ).lazy(),
    }

    registry_data_df = {
        "ndw_outgoing": pl.DataFrame(
            {
                "siret": ["12345678901234", "98765432109876", "12345678901234"],
                "destination_company_org_id": ["98765432109876", "98765432109876", "56789012345678"],
                "dispatch_date": [
                    datetime(2023, 2, 1, tzinfo=tz),
                    datetime(2023, 4, 20, tzinfo=tz),
                    datetime(2023, 6, 10, tzinfo=tz),
                ],
                "weight_value": [None, 25, 35],
                "volume": [15, None, None],
                "waste_code": ["04 01 01", "04 01 02", "02 01 03"],
                "waste_description": ["Déchet AA", "Déchet BB", None],
                "transporters_org_ids": [
                    ["98765432109876"],
                    ["12345678901234", "98765432109876"],
                    ["98765432109876"],
                ],
                "operation_code": ["R1", "R2", "D5"],
            }
        ).lazy()
    }

    icpe_data_df = pl.DataFrame({"rubrique": ["2770", "2771"]}).lazy()
    return {
        "bs_data": bs_data_dfs,
        "transporters_data": transporters_data_df,
        "registry_data": registry_data_df,
        "icpe_data": icpe_data_df,
    }


@pytest.fixture
def sample_data_date_interval():
    """Sample data date interval for filtering"""
    return (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz))


def test_preprocess_bs_data(sample_data, sample_data_date_interval):
    """Test preprocessing of BS data for dangerous waste"""
    processor = IncineratorOutgoingWasteProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_data["bs_data"],
        transporters_data_df=sample_data["transporters_data"],
        icpe_data=sample_data["icpe_data"],
        registry_outgoing_data=None,  # Testing only BS data
        data_date_interval=sample_data_date_interval,
    )
    processor._preprocess_bs_data()

    preprocessed_data = processor.preprocessed_data["dangerous"]
    assert len(preprocessed_data) == 5

    expected_data = pl.DataFrame(
        [
            {
                "waste_code": "01 01 01*",
                "recipient_company_siret": "43210987654321",
                "processing_operation_code": "D10",
                "quantity": 30.0,
                "waste_name": "Déchet A",
            },
            {
                "waste_code": "01 01 03*",
                "recipient_company_siret": "87654321098765",
                "processing_operation_code": "D5",
                "quantity": 9.3,
                "waste_name": "Déchet B",
            },
            {
                "waste_code": "02 01 01*",
                "recipient_company_siret": "87654321098765",
                "processing_operation_code": "D10",
                "quantity": 12.5,
                "waste_name": "Déchet C",
            },
            {
                "waste_code": "04 01 01*",
                "recipient_company_siret": "43210987654321",
                "processing_operation_code": "D10",
                "quantity": 3.18,
                "waste_name": "Déchet A",
            },
            {
                "waste_code": "04 01 03*",
                "recipient_company_siret": "87654321098769",
                "processing_operation_code": "R1",
                "quantity": 19.0,
                "waste_name": "Déchet B",
            },
        ]
    )

    assert_frame_equal(preprocessed_data, expected_data)


def test_preprocess_registry_statements_data(sample_data, sample_data_date_interval):
    """Test preprocessing of registry data for non-dangerous waste"""
    processor = IncineratorOutgoingWasteProcessor(
        company_siret="12345678901234",
        bs_data_dfs={},
        transporters_data_df={},
        icpe_data=sample_data["icpe_data"],
        registry_outgoing_data=sample_data["registry_data"]["ndw_outgoing"],
        data_date_interval=sample_data_date_interval,
    )
    processor._preprocess_registry_statements_data()

    preprocessed_data = processor.preprocessed_data["non_dangerous"]
    assert len(preprocessed_data) == 2

    expected_data = pl.DataFrame(
        [
            {
                "waste_code": "02 01 03",
                "destination_company_org_id": "56789012345678",
                "operation_code": "D5",
                "quantity": 35.0,
                "waste_name": "",
                "unit": "t",
            },
            {
                "waste_code": "04 01 01",
                "destination_company_org_id": "98765432109876",
                "operation_code": "R1",
                "quantity": 15.0,
                "waste_name": "Déchet AA",
                "unit": "m³",
            },
        ]
    )

    assert preprocessed_data.equals(expected_data)


def test_is_incinerator(sample_data):
    """Test the incinerator detection method"""
    processor = IncineratorOutgoingWasteProcessor(
        company_siret="12345678901234",
        bs_data_dfs={},
        transporters_data_df={},
        icpe_data=sample_data["icpe_data"],
        registry_outgoing_data=None,
        data_date_interval=(datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 12, 31, tzinfo=tz)),
    )
    assert processor.is_incinerator(dangerous_waste=True), "Incinerator detection failed for dangerous waste"
    assert processor.is_incinerator(dangerous_waste=False), "Incinerator detection failed for non-dangerous waste"


def test_build_with_no_data(sample_data):
    """Test build method when no data is available"""
    processor = IncineratorOutgoingWasteProcessor(
        company_siret="87654321098765",
        bs_data_dfs={},
        transporters_data_df={},
        icpe_data=sample_data["icpe_data"],
        registry_outgoing_data=None,
        data_date_interval=(datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 12, 31, tzinfo=tz)),
    )
    result = processor.build()
    assert result == {}, "Expected empty result when no data is available"
    assert processor._check_data_empty()


def test_build_with_data(
    sample_data,
    sample_data_date_interval,
):
    """Test build method with both BS and registry data"""
    processor = IncineratorOutgoingWasteProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_data["bs_data"],
        transporters_data_df=sample_data["transporters_data"],
        icpe_data=sample_data["icpe_data"],
        registry_outgoing_data=sample_data["registry_data"]["ndw_outgoing"],  # Testing only BS data
        data_date_interval=sample_data_date_interval,
    )
    result = processor.build()
    assert len(result["dangerous"]) > 0, "No dangerous waste data in result"
    assert len(result["non_dangerous"]) > 0, "No non-dangerous waste data in result"

    expected_data = json.load(
        (EXPECTED_FILES_PATH / "incinerator_outgoing_waste_build_data_expected.json").open(encoding="utf-8")
    )

    assert result == expected_data
