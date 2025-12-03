from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from sheets.constants import BSDA, BSDD

from ..graph_processors.html_components import WasteProcessingWithoutICPERubriqueProcessor

tz = ZoneInfo("Europe/Paris")


# Example data for testing
@pytest.fixture
def sample_data():
    # Sample data for ICPE data with different "rubriques"
    icpe_data = pl.LazyFrame({"rubrique": ["2770", "2791-1", "2718-1"]})

    # Sample bordereau data for BSDD
    bsdd_data = pl.LazyFrame(
        {
            "recipient_company_siret": ["12345678900000", "12345678900000", "12345678900000"],
            "processing_operation_code": ["D8", "D5", "D10"],
            "processed_at": [
                datetime(2023, 1, 1, tzinfo=tz),
                datetime(2023, 2, 2, tzinfo=tz),
                datetime(2023, 4, 3, tzinfo=tz),
            ],
            "quantity_received": [12.5, 22.0, 30.1],
            "quantity_refused": [0.0, 2.0, 25.1],
        }
    )

    # Sample bordereau data for BSDA
    bsda_data = pl.LazyFrame(
        {
            "recipient_company_siret": ["12345678900000", "12345678900000", "12345678900000"],
            "processing_operation_code": ["D5", "R2", "D5"],
                "processed_at": [
                    datetime(2023, 2, 2, tzinfo=tz),
                    datetime(2023, 4, 3, tzinfo=tz),
                    datetime(2023, 4, 15, tzinfo=tz),  # Changed to be within date interval
                ],
            "quantity_received": [5.0, 15.0, 10.0],
            "waste_code": ["17 06 05*", "02 01 01*", "17 06 01*"],  # First and third are asbestos
        }
    )

    # Sample RNDTS incoming data
    rndts_incoming_data = pl.LazyFrame(
        {
            "siret": ["12345678900000", "12345678900000", "12345678900000"],
            "reception_date": [
                datetime(2023, 1, 1, tzinfo=tz),
                datetime(2023, 2, 2, tzinfo=tz),
                datetime(2023, 3, 3, tzinfo=tz),
            ],
            "operation_code": ["D5", "R1", "D10"],
            "weight_value": [30.0, 20.0, 15.0],
        }
    )

    bs_data_dfs = {BSDD: bsdd_data, BSDA: bsda_data}
    data_date_interval = (
        datetime(2023, 1, 1, tzinfo=tz),
        datetime(2023, 5, 31, tzinfo=tz),  # Extended to include May 5th
    )

    return bs_data_dfs, rndts_incoming_data, icpe_data, data_date_interval


def test_initialization(sample_data):
    """Test that the processor initializes with correct parameters."""

    bs_data_dfs, rndts_incoming_data, icpe_data, data_date_interval = sample_data
    processor = WasteProcessingWithoutICPERubriqueProcessor(
        company_siret="12345678900000",
        bs_data_dfs=bs_data_dfs,
        registry_incoming_data=rndts_incoming_data,
        icpe_data=icpe_data,
        data_date_interval=data_date_interval,
        packagings_data_df=None,
    )
    assert processor.siret == "12345678900000"
    assert processor.data_date_interval is not None
    assert isinstance(processor.bs_data_dfs, dict)
    assert isinstance(processor.icpe_data, pl.LazyFrame)


def test_preprocess_data_multi_rubriques(sample_data):
    """Test that multiple rubrique processing works correctly."""
    bs_data_dfs, rndts_incoming_data, icpe_data, data_date_interval = sample_data
    processor = WasteProcessingWithoutICPERubriqueProcessor(
        company_siret="12345678900000",
        bs_data_dfs=bs_data_dfs,
        registry_incoming_data=rndts_incoming_data,
        icpe_data=icpe_data,
        data_date_interval=data_date_interval,
        packagings_data_df=None,
    )

    processor._preprocess_data_multi_rubriques()
    preprocessed_data = processor.preprocessed_data["dangerous"]
    assert len(preprocessed_data) == 1

    item = preprocessed_data[0]
    expected_output = {
        "missing_rubriques": "2760-1, 2760-2",
        "num_missing_rubriques": 2,
        "found_processing_codes": "D5",
        "num_found_processing_codes": 1,
        "bs_list": pl.DataFrame(
            {
                "recipient_company_siret": ["12345678900000", "12345678900000", "12345678900000"],
                "processing_operation_code": ["D5", "D5", "D5"],
                "processed_at": [
                    datetime(2023, 2, 2, tzinfo=tz),
                    datetime(2023, 2, 2, tzinfo=tz),
                    datetime(2023, 4, 15, tzinfo=tz),  # Changed to be within date interval
                ],
                "quantity_received": [22.0, 5.0, 10.0],
                "quantity_refused": [2.0, None, None],
                "bs_type": ["BSDD", "BSDA", "BSDA"],
                "waste_code": [None, "17 06 05*", "17 06 01*"],  # BSDD has None, BSDA has asbestos codes
            }
        ),
        "stats": {"total_bs": "3", "total_quantity": "35"},
    }

    assert item.keys() == expected_output.keys()

    for key in item.keys():
        if key == "bs_list":
            # Dataframes equality test
            assert_frame_equal(item[key], expected_output[key])
        else:
            assert item[key] == expected_output[key]


def test_preprocess_data_single_rubrique(sample_data):
    """Test that single rubrique processing works correctly."""
    bs_data_dfs, rndts_incoming_data, icpe_data, data_date_interval = sample_data
    processor = WasteProcessingWithoutICPERubriqueProcessor(
        company_siret="12345678900000",
        bs_data_dfs=bs_data_dfs,
        registry_incoming_data=rndts_incoming_data,
        icpe_data=icpe_data,
        data_date_interval=data_date_interval,
        packagings_data_df=None,
    )

    processor._preprocess_data_single_rubrique()
    dangerous_data = processor.preprocessed_data["dangerous"]
    assert len(dangerous_data) == 1

    item = dangerous_data[0]

    expected_output = {
        "missing_rubriques": "2790",
        "num_missing_rubriques": 1,
        "found_processing_codes": "D8, R2",
        "num_found_processing_codes": 2,
        "bs_list": pl.DataFrame(
            {
                "recipient_company_siret": ["12345678900000", "12345678900000"],
                "processing_operation_code": ["R2", "D8"],
                "processed_at": [datetime(2023, 4, 3, tzinfo=tz), datetime(2023, 1, 1, tzinfo=tz)],
                "quantity_received": [15.0, 12.5],
                "quantity_refused": [None, 0.0],
                "bs_type": ["BSDA", "BSDD"],
            }
        ),
        "stats": {"total_bs": "2", "total_quantity": "27.5"},
    }

    assert item.keys() == expected_output.keys()
    for key in item.keys():
        if key == "bs_list":
            # Dataframes equality test
            assert_frame_equal(item[key], expected_output[key])
        else:
            assert item[key] == expected_output[key]


def test_preprocess_non_dangerous_rubriques(sample_data):
    """Test that non-dangerous rubrique processing works correctly."""
    bs_data_dfs, rndts_incoming_data, icpe_data, data_date_interval = sample_data
    processor = WasteProcessingWithoutICPERubriqueProcessor(
        company_siret="12345678900000",
        bs_data_dfs=bs_data_dfs,
        registry_incoming_data=rndts_incoming_data,
        icpe_data=icpe_data,
        data_date_interval=data_date_interval,
        packagings_data_df=None,
    )
    processor._preprocess_non_dangerous_rubriques()
    non_dangerous_data = processor.preprocessed_data["non_dangerous"]

    assert len(non_dangerous_data) == 2

    expected_output = [
        {
            "missing_rubriques": "2760-2",
            "num_missing_rubriques": 1,
            "found_processing_codes": "D5",
            "num_found_processing_codes": 1,
            "statements_list": pl.DataFrame(
                {
                    "siret": ["12345678900000"],
                    "reception_date": [datetime(2023, 1, 1, tzinfo=tz)],
                    "operation_code": ["D5"],
                    "weight_value": [30.0],
                }
            ),
            "stats": {"total_statements": "1", "total_quantity": "30"},
        },
        {
            "missing_rubriques": "2771",
            "num_missing_rubriques": 1,
            "found_processing_codes": "D10, R1",  # Now includes both D10 and R1
            "num_found_processing_codes": 2,
            "statements_list": pl.DataFrame(
                {
                    "siret": ["12345678900000", "12345678900000"],
                    "reception_date": [datetime(2023, 3, 3, tzinfo=tz), datetime(2023, 2, 2, tzinfo=tz)],
                    "operation_code": ["D10", "R1"],
                    "weight_value": [15.0, 20.0],
                }
            ),
            "stats": {"total_statements": "2", "total_quantity": "35"},
        },
    ]

    for item, expected_item in zip(non_dangerous_data, expected_output):
        assert item.keys() == expected_item.keys()

        for key in item.keys():
            if key == "statements_list":
                # Dataframes equality test
                assert_frame_equal(item[key], expected_item[key])
            else:
                assert item[key] == expected_item[key]


def test_preprocess_data_multi_rubriques_without_quantity_refused(sample_data):
    """Test that multiple rubrique processing works correctly with asbestos filtering."""
    bs_data_dfs, rndts_incoming_data, icpe_data, data_date_interval = sample_data
    # Create BSDA-only data with asbestos and non-asbestos waste
    bsda_only_data = {
        BSDA: pl.LazyFrame(
            {
                "recipient_company_siret": ["12345678900000", "12345678900000", "12345678900000"],
                "processing_operation_code": ["D5", "D5", "D5"],
                "processed_at": [
                    datetime(2023, 2, 2, tzinfo=tz),
                    datetime(2023, 4, 15, tzinfo=tz),
                    datetime(2023, 4, 20, tzinfo=tz),
                ],
                "quantity_received": [5.0, 10.0, 8.0],
                "waste_code": ["17 06 05*", "17 06 01*", "02 01 01*"],  # First two are asbestos, third is not
            }
        )
    }
    processor = WasteProcessingWithoutICPERubriqueProcessor(
        company_siret="12345678900000",
        bs_data_dfs=bsda_only_data,
        registry_incoming_data=None,
        icpe_data=pl.LazyFrame({"rubrique": ["2791-1", "2718-1"]}),
        data_date_interval=data_date_interval,
        packagings_data_df=None,
    )

    processor._preprocess_data_multi_rubriques()
    preprocessed_data = processor.preprocessed_data["dangerous"]
    assert len(preprocessed_data) == 1

    item = preprocessed_data[0]
    expected_output = {
        "missing_rubriques": "2760-1, 2760-2",
        "num_missing_rubriques": 2,
        "found_processing_codes": "D5",
        "num_found_processing_codes": 1,
        "bs_list": pl.DataFrame(
            {
                "recipient_company_siret": ["12345678900000", "12345678900000"],
                "processing_operation_code": ["D5", "D5"],
                "processed_at": [datetime(2023, 2, 2, tzinfo=tz), datetime(2023, 4, 15, tzinfo=tz)],
                "quantity_received": [5.0, 10.0],
                "bs_type": ["BSDA", "BSDA"],
                "waste_code": ["17 06 05*", "17 06 01*"],  # Only asbestos codes
            }
        ),
        "stats": {"total_bs": "2", "total_quantity": "15"},
    }

    assert item.keys() == expected_output.keys()

    for key in item.keys():
        if key == "bs_list":
            # Dataframes equality test
            assert_frame_equal(item[key], expected_output[key])
        else:
            assert item[key] == expected_output[key]


def test_check_data_empty():
    """Test that the data check function works correctly."""

    processor = WasteProcessingWithoutICPERubriqueProcessor(
        company_siret="12345678900000",
        bs_data_dfs={
            BSDD: None,
            BSDA: pl.LazyFrame(
                {
                    "recipient_company_siret": [],
                    "processing_operation_code": [],
                    "processed_at": [],
                    "quantity_received": [],
                },
                schema={
                    "recipient_company_siret": pl.String,
                    "processing_operation_code": pl.String,
                    "processed_at": pl.Datetime(time_zone="Europe/Paris"),
                    "quantity_received": pl.Float64,
                },
            ),
        },
        registry_incoming_data=None,
        icpe_data=None,
        data_date_interval=(
            datetime(2023, 1, 1, tzinfo=tz),
            datetime(2023, 4, 30, tzinfo=tz),
        ),
        packagings_data_df=None,
    )
    # Trigger data preprocessing
    processor._preprocess_data()
    assert processor._check_data_empty() is True
