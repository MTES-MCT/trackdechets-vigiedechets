from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from sheets.constants import BSDA, BSDASRI, BSDD, BSFF
from sheets.data_extract import load_waste_code_data

from ..graph_processors.html_components_processors import (
    WasteFlowsTableProcessor,
)  # Adjust the import to your actual module
from .constants import EXPECTED_FILES_PATH

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_data() -> dict:
    # Creating sample data for bs_data_dfs, transporters_data_df, rndts_data, waste_codes_df, and packagings_data
    bs_data_dfs = {
        BSDD: pl.LazyFrame(
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
                "quantity_received": [10.0, 20.0, 30.0, 19.0],
                "quantity_refused": [3.0, None, 30.0, 7.0],
            }
        ),
        BSDA: pl.LazyFrame(
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
                "quantity_received": [12.5, 32, 9.3, 10],
            }
        ),
        BSFF: pl.LazyFrame(
            {
                "id": [8, 5, 6, 2],
                "emitter_company_siret": ["12345678901234", "98765432109876", "12345678901234", "87654321098765"],
                "recipient_company_siret": ["87654321098765", "12345678901234", "87654321098765", "97654321098765"],
                "received_at": [
                    datetime(2023, 2, 1, tzinfo=tz),
                    datetime(2023, 4, 20, tzinfo=tz),
                    datetime(2023, 6, 10, tzinfo=tz),
                    datetime(2023, 6, 14, tzinfo=tz),
                ],
                "waste_code": ["03 01 01*", "03 01 02*", "03 01 03*", "03 01 03*"],
            }
        ),
        BSDASRI: pl.LazyFrame(
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
        ),
    }

    transporters_data_df = {
        BSDD: pl.LazyFrame(
            {
                "bs_id": [1, 2, 3, 4],
                "transporter_company_siret": ["56789012345678", "56789012345678", "97654321098765", "12345678901234"],
                "sent_at": [
                    datetime(2023, 1, 10, tzinfo=tz),
                    datetime(2023, 3, 15, tzinfo=tz),
                    datetime(2023, 5, 20, tzinfo=tz),
                    datetime(2023, 5, 20, tzinfo=tz),
                ],
                "quantity_received": [10, 20, 30, 19],
            }
        ),
        BSDA: pl.LazyFrame(
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
        ),
        BSFF: pl.LazyFrame(
            {
                "bs_id": [8, 5, 6, 2],
                "transporter_company_siret": [
                    "56789012345678",
                    "56789012345678",
                    "12345678901234",
                    "12345678901234",
                ],  # The third is to test the case where the company as emitted and transported the same waste (multiple flow status)
                "sent_at": [
                    datetime(2023, 1, 10, tzinfo=tz),
                    datetime(2023, 3, 15, tzinfo=tz),
                    datetime(2023, 5, 20, tzinfo=tz),
                    datetime(2023, 5, 20, tzinfo=tz),
                ],
            }
        ),
    }

    packagings_data = pl.LazyFrame(
        {
            "bsff_id": [8, 8, 5, 6, 2],
            "acceptation_weight": [3.0, 1.001, 1.0, 2.4, 5.0],
            "acceptation_date": [
                datetime(2023, 2, 1, tzinfo=tz),
                datetime(2023, 2, 1, tzinfo=tz),
                datetime(2023, 4, 20, tzinfo=tz),
                datetime(2023, 6, 10, tzinfo=tz),
                datetime(2023, 6, 10, tzinfo=tz),
            ],
        }
    )

    rndts_data = {
        "ndw_incoming": pl.LazyFrame(
            {
                "siret": ["12345678901234", "12345678901234", "98765432109876"],
                "reception_date": [
                    datetime(2023, 1, 10, tzinfo=tz),
                    datetime(2023, 3, 15, tzinfo=tz),
                    datetime(2023, 5, 20, tzinfo=tz),
                ],
                "weight_value": [10.0, None, 30.0],
                "volume": [None, 20.0, None],
                "waste_code": ["03 01 01", "03 01 02", "03 01 01"],
                "transporters_org_ids": [["98765432109876"], ["98765432109876"], ["12345678901234"]],
            }
        ),
        "ndw_outgoing": pl.LazyFrame(
            {
                "siret": ["12345678901234", "98765432109876", "12345678901234"],
                "dispatch_date": [
                    datetime(2023, 2, 1, tzinfo=tz),
                    datetime(2023, 4, 20, tzinfo=tz),
                    datetime(2023, 6, 10, tzinfo=tz),
                ],
                "weight_value": [None, 25.0, 35.0],
                "volume": [15.0, None, None],
                "waste_code": ["04 01 01", "04 01 02", "02 01 03"],
                "transporters_org_ids": [
                    ["98765432109876"],
                    ["12345678901234", "98765432109876"],
                    ["98765432109876"],
                ],
            }
        ),
        "excavated_land_incoming": pl.LazyFrame(
            {
                "siret": ["12345678901234", "12345678901234", "98765432109876"],
                "reception_date": [
                    datetime(2023, 2, 10, tzinfo=tz),
                    datetime(2023, 3, 18, tzinfo=tz),
                    datetime(2023, 5, 21, tzinfo=tz),
                ],
                "weight_value": [9.7, None, 18.0],
                "volume": [None, 12.0, None],
                "waste_code": ["03 01 01", "03 01 02", "03 01 03"],
                "transporters_org_ids": [["98765432109876"], ["98765432109876"], ["12345678901234"]],
            }
        ),
        "excavated_land_outgoing": pl.LazyFrame(
            {
                "siret": ["12345678901234", "98765432109876", "12345678901234"],
                "dispatch_date": [
                    datetime(2023, 2, 1, tzinfo=tz),
                    datetime(2023, 2, 20, tzinfo=tz),
                    datetime(2023, 4, 17, tzinfo=tz),
                ],
                "weight_value": [None, 25.0, 35.0],
                "volume": [15.0, None, None],
                "waste_code": ["05 01 01", "03 01 02", "02 01 03"],
                "transporters_org_ids": [
                    ["98765432109876"],
                    ["12345678901234", "98765432109876"],
                    ["98765432109876"],
                ],
            }
        ),
    }

    return {
        "bs_data_dfs": bs_data_dfs,
        "transporters_data_df": transporters_data_df,
        "rndts_data": rndts_data,
        "packagings_data": packagings_data,
    }


@pytest.fixture
def waste_code_data() -> pl.LazyFrame:
    return load_waste_code_data()


def test_preprocess_bs_data(sample_data: dict, waste_code_data: pl.LazyFrame):
    processor = WasteFlowsTableProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_data["bs_data_dfs"],
        transporters_data_df=sample_data["transporters_data_df"],
        registry_data=sample_data["rndts_data"],
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
        waste_codes_df=waste_code_data,
        packagings_data=sample_data["packagings_data"],
    )

    bs_data = processor._preprocess_bs_data()

    expected_output = pl.DataFrame(
        {
            "waste_code": [
                "01 01 01*",
                "01 01 03*",
                "01 01 03*",
                "01 01 03*",
                "02 01 01*",
                "02 01 01*",
                "02 01 02*",
                "03 01 01*",
                "03 01 02*",
                "03 01 03*",
                "03 01 03*",
                "04 01 01*",
                "04 01 03*",
                "04 01 03*",
            ],
            "flow_status": [
                "outgoing",
                "incoming",
                "outgoing",
                "transported",
                "outgoing",
                "transported",
                "incoming",
                "outgoing",
                "incoming",
                "outgoing",
                "transported",
                "outgoing",
                "incoming",
                "outgoing",
            ],
            "quantity_received": [27.0, 0.0, 9.3, 12.0, 12.5, 10.0, 32.0, 4.001, 1.0, 2.4, 7.4, 7.3, 0.54, 19.0],
            "unit": ["t", "t", "t", "t", "t", "t", "t", "t", "t", "t", "t", "t", "t", "t"],
        }
    )
    assert bs_data is not None
    assert_frame_equal(bs_data.sort(["waste_code", "flow_status"]).collect(), expected_output)


def test_preprocess_rndts_data(sample_data: dict, waste_code_data: pl.LazyFrame):
    processor = WasteFlowsTableProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_data["bs_data_dfs"],
        transporters_data_df=sample_data["transporters_data_df"],
        registry_data=sample_data["rndts_data"],
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
        waste_codes_df=waste_code_data,
        packagings_data=sample_data["packagings_data"],
    )

    preprocessed_rndts_data = processor._preprocess_registry_data()

    expected_output = pl.DataFrame(
        {
            "waste_code": [
                "03 01 01",
                "03 01 02",
                "03 01 01",
                "02 01 03",
                "04 01 01",
                "04 01 02",
                "03 01 01",
                "03 01 02",
                "03 01 03",
                "02 01 03",
                "05 01 01",
                "03 01 02",
            ],
            "quantity_received": [10.0, 20.0, 30.0, 35.0, 15.0, 25.0, 9.7, 12.0, 18.0, 35.0, 15.0, 25.0],
            "unit": ["t", "m³", "t", "t", "m³", "t", "t", "m³", "t", "t", "m³", "t"],
            "flow_status": [
                "incoming",
                "incoming",
                "transported_incoming",
                "outgoing",
                "outgoing",
                "transported_outgoing",
                "incoming",
                "incoming",
                "transported_incoming",
                "outgoing",
                "outgoing",
                "transported_outgoing",
            ],
        }
    )
    assert preprocessed_rndts_data is not None
    assert_frame_equal(preprocessed_rndts_data.collect(), expected_output)


def test_preprocess_data(sample_data: dict, waste_code_data: pl.LazyFrame):
    processor = WasteFlowsTableProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_data["bs_data_dfs"],
        transporters_data_df=sample_data["transporters_data_df"],
        registry_data=sample_data["rndts_data"],
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
        waste_codes_df=waste_code_data,
        packagings_data=sample_data["packagings_data"],
    )

    processor._preprocess_data()
    preprocessed_df = processor.preprocessed_df

    expected_output = pl.read_csv(
        EXPECTED_FILES_PATH / "waste_flow_preprocessed_data_expected.csv", infer_schema=False
    )
    assert preprocessed_df is not None
    assert_frame_equal(preprocessed_df, expected_output)


def test_empty_data():
    processor = WasteFlowsTableProcessor(
        company_siret="12345678901234",
        bs_data_dfs={},
        transporters_data_df={},
        registry_data={},
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
        waste_codes_df=pl.LazyFrame(),
        packagings_data=None,
    )

    processor._preprocess_data()
    preprocessed_df = processor.preprocessed_df

    assert preprocessed_df is None


def test_empty_bs_data_with_transport_data(waste_code_data: pl.LazyFrame):
    transport_df = pl.LazyFrame(
        {
            "id": ["1", "2"],
            "bs_id": ["5", "6"],
            "sent_at": [datetime(2023, 2, 2, tzinfo=tz), datetime(2023, 5, 2, tzinfo=tz)],
            "transporter_company_siret": ["12345678901234", "12345678901234"],
            "transporter_transport_mode": ["ROAD", "ROAD"],
            "quantity_received": [12.5, 11.3],
            "waste_code": ["13 03 10*", "14 06 01*"],
        }
    )
    processor = WasteFlowsTableProcessor(
        company_siret="12345678901234",
        bs_data_dfs={
            BSDD: pl.LazyFrame(
                {
                    e: []
                    for e in [
                        "id",
                        "created_at",
                        "sent_at",
                        "received_at",
                        "emitter_company_siret",
                        "emitter_company_address",
                        "recipient_company_siret",
                        "waste_detail_quantity",
                        "waste_code",
                        "quantity_received",
                        "status",
                    ]
                }
            )
        },
        transporters_data_df={BSDD: transport_df},
        registry_data={},
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
        waste_codes_df=waste_code_data,
        packagings_data=None,
    )

    processor._preprocess_data()
    preprocessed_df = processor.preprocessed_df

    expected_output = pl.DataFrame(
        {
            "waste_code": ["13 03 10*", "14 06 01*"],
            "description": ["autres huiles isolantes et fluides caloporteurs", "chlorofluorocarbones, HCFC, HFC"],
            "flow_status": ["transported", "transported"],
            "quantity_received": ["12.5", "11.3"],
            "unit": ["t", "t"],
        }
    )
    assert_frame_equal(preprocessed_df, expected_output)


def test_empty_packagings_data_with_bsff_and_transport_data(sample_data: dict, waste_code_data: pl.LazyFrame):
    processor = WasteFlowsTableProcessor(
        company_siret="12345678901234",
        bs_data_dfs={BSFF: sample_data["bs_data_dfs"][BSFF]},
        transporters_data_df={BSFF: sample_data["transporters_data_df"][BSFF]},
        registry_data={},
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
        waste_codes_df=waste_code_data,
        packagings_data=None,
    )

    processor._preprocess_data()
    preprocessed_df = processor.preprocessed_df

    assert preprocessed_df is None


def test_build(sample_data: dict, waste_code_data: pl.LazyFrame):
    processor = WasteFlowsTableProcessor(
        company_siret="12345678901234",
        bs_data_dfs=sample_data["bs_data_dfs"],
        transporters_data_df=sample_data["transporters_data_df"],
        registry_data=sample_data["rndts_data"],
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
        waste_codes_df=waste_code_data,
        packagings_data=sample_data["packagings_data"],
    )

    result = processor.build()

    assert isinstance(result, list)
    assert len(result) == 22
    for record in result:
        assert "waste_code" in record
        assert "description" in record
        assert "flow_status" in record
        assert "quantity_received" in record
        assert "unit" in record
