from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from polars.exceptions import ColumnNotFoundError
from polars.testing import assert_frame_equal

from ..graph_processors.html_components import SSDProcessor

tz = ZoneInfo("Europe/Paris")


# Sample data fixture
@pytest.fixture
def sample_ssd_data():
    data = {
        "siret": [
            "12345678901234",
            "12345678901234",
            "12345678901234",
            "12345678901234",
            "12345678901234",
            "56789012345678",
            "56789012345678",
            "12345678901234",
            "12345678901234",
            "56789012345678",
        ],
        "dispatch_date": [
            datetime(2023, 1, 10, tzinfo=tz),
            datetime(2023, 2, 5, tzinfo=tz),
            datetime(2023, 3, 15, tzinfo=tz),
            datetime(2023, 3, 20, tzinfo=tz),
            datetime(2023, 4, 10, tzinfo=tz),
            datetime(2023, 4, 5, tzinfo=tz),
            datetime(2023, 5, 25, tzinfo=tz),
            datetime(2023, 6, 30, tzinfo=tz),
            datetime(2023, 7, 1, tzinfo=tz),
            datetime(2023, 2, 15, tzinfo=tz),
        ],
        "weight_value": [10.0, 20.5, None, 5.0, None, 35.0, 50.0, 45.0, None, 30.2],
        "volume": [None, None, 15.0, None, 25.0, None, None, None, 5.0, None],
        "waste_code": [
            "13 01 10*",
            "13 01 10*",
            "16 01 14*",
            "16 01 14*",
            "13 07 03*",
            "13 07 03*",
            "13 01 10*",
            "13 01 10*",
            "13 02 05*",
            "13 02 05*",
        ],
        "waste_description": [
            "HUILE CLAIRE USAGEE",
            "HUILE CLAIRE USAGEE",
            "LIQUIDE DE REFROIDISSEMENT USAGE",
            "LIQUIDE DE REFROIDISSEMENT USAGE",
            "LIQUIDE PETROLIER",
            "LIQUIDE PETROLIER",
            "HUILE CLAIRE USAGEE",
            "HUILE CLAIRE USAGEE",
            "Huiles moteur, de boite de vitesses et de lubrification non chlorees a base minerale",
            "Huiles moteur, de boite de vitesses et de lubrification non chlorees a base minerale",
        ],
    }

    return pl.LazyFrame(data)


def test_preprocess_data(sample_ssd_data):
    processor = SSDProcessor(
        company_siret="12345678901234",
        ssd_data=sample_ssd_data,
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
    )

    processor._preprocess_data()

    preprocessed_data = processor.preprocessed_data

    assert preprocessed_data is not None, "Preprocessed data should not be empty."

    expected_output = pl.DataFrame(
        {
            "waste_code": ["13 01 10*", "13 07 03*", "16 01 14*", "13 01 10*", "13 07 03*", "16 01 14*"],
            "quantity": [75.5, 0.0, 5.0, 0.0, 25.0, 15.0],
            "waste_description": [
                "HUILE CLAIRE USAGEE",
                "LIQUIDE PETROLIER",
                "LIQUIDE DE REFROIDISSEMENT USAGE",
                "HUILE CLAIRE USAGEE",
                "LIQUIDE PETROLIER",
                "LIQUIDE DE REFROIDISSEMENT USAGE",
            ],
            "unit": ["t", "t", "t", "m³", "m³", "m³"],
        }
    )
    # Check aggregated quantities and sorting
    assert_frame_equal(preprocessed_data, expected_output)


def test_empty_ssd_data():
    processor = SSDProcessor(
        company_siret="12345678901234",
        ssd_data=None,
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
    )

    processor._preprocess_data()

    assert processor._check_data_empty(), "Data should be considered empty when SSD data is None."


def test_data_outside_date_range(sample_ssd_data):
    processor = SSDProcessor(
        company_siret="12345678901234",
        ssd_data=sample_ssd_data,
        data_date_interval=(
            datetime(2023, 7, 2, tzinfo=tz),
            datetime(2023, 8, 1, tzinfo=tz),
        ),  # No data falls in this range
    )

    processor._preprocess_data()

    assert processor._check_data_empty(), "Data should be empty when no data falls within the specified date range."


def test_correct_serialization(sample_ssd_data):
    processor = SSDProcessor(
        company_siret="12345678901234",
        ssd_data=sample_ssd_data,
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
    )

    processor._preprocess_data()

    serialized_data = processor._serialize_stats()

    assert isinstance(serialized_data, list), "Serialized data should be a list of dictionaries."
    expected_output = [
        {"waste_code": "13 01 10*", "waste_name": "HUILE CLAIRE USAGEE", "quantity": "75.5", "unit": "t"},
        {"waste_code": "13 07 03*", "waste_name": "LIQUIDE PETROLIER", "quantity": "0", "unit": "t"},
        {"waste_code": "16 01 14*", "waste_name": "LIQUIDE DE REFROIDISSEMENT USAGE", "quantity": "5", "unit": "t"},
        {"waste_code": "13 01 10*", "waste_name": "HUILE CLAIRE USAGEE", "quantity": "0", "unit": "m³"},
        {"waste_code": "13 07 03*", "waste_name": "LIQUIDE PETROLIER", "quantity": "25", "unit": "m³"},
        {"waste_code": "16 01 14*", "waste_name": "LIQUIDE DE REFROIDISSEMENT USAGE", "quantity": "15", "unit": "m³"},
    ]
    assert serialized_data == expected_output


def test_incorrect_data_format():
    data = {
        "siret": ["12345678901234"],
        "dispatch_date": ["Not a datetime"],  # Incorrect date format
        "weight_value": [10.0],
        "volume": [None],
        "waste_code": ["01 01 01"],
        "waste_description": ["Waste Type A"],
    }

    ssd_data_df = pl.LazyFrame(data)

    processor = SSDProcessor(
        company_siret="12345678901234",
        ssd_data=ssd_data_df,
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
    )

    with pytest.raises(Exception):
        processor._preprocess_data()


def test_missing_columns():
    data = {
        "siret": ["12345678901234"],
        "weight_value": [10.0],
        "volume": [None],
        "waste_code": ["01 01 01"],
    }

    ssd_data_df = pl.LazyFrame(data)

    processor = SSDProcessor(
        company_siret="12345678901234",
        ssd_data=ssd_data_df,
        data_date_interval=(datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 6, 30, tzinfo=tz)),
    )

    with pytest.raises(ColumnNotFoundError):
        processor._preprocess_data()
