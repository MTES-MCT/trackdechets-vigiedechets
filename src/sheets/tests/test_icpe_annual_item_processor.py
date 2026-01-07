from datetime import datetime
from zoneinfo import ZoneInfo

import plotly.graph_objects as go
import polars as pl
import pytest
from polars.exceptions import ColumnNotFoundError, InvalidOperationError
from polars.testing import assert_frame_equal

from ..graph_processors.plotly_components import ICPEAnnualItemProcessor

tz = ZoneInfo("Europe/Paris")


# Sample data fixture
@pytest.fixture
def sample_icpe_data():
    data = {
        "day_of_processing": [
            datetime(2023, 1, 1, tzinfo=tz),
            datetime(2023, 1, 2, tzinfo=tz),
            datetime(2023, 1, 3, tzinfo=tz),
            datetime(2023, 1, 4, tzinfo=tz),
            datetime(2023, 1, 5, tzinfo=tz),
            datetime(2023, 1, 6, tzinfo=tz),
            datetime(2023, 1, 7, tzinfo=tz),
            datetime(2023, 1, 8, tzinfo=tz),
            datetime(2023, 1, 9, tzinfo=tz),
            datetime(2023, 1, 10, tzinfo=tz),
        ],
        "processed_quantity": [10, 20, 15, 0, 5, 0, 25, 30, 0, 5],
        "authorized_quantity": [50, 50, 50, 50, 50, 50, 50, 50, 50, 50],
        "target_quantity": [25, 25, 25, 25, 25, 25, 25, 25, 25, 25],
    }

    return pl.DataFrame(data).lazy()


def test_preprocess_data(sample_icpe_data):
    """
    GIVE daily processed ICPE item data for multiple days between 2023-01-01 and 2023-01-10
    WHEN the _preprocess_data method is called on ICPEAnnualItemProcessor with the data date interval (2023-01-01, 2023-01-09)
    THEN the resulting preprocessed_df contains sorted, grouped, and cumulative quantities as expected, matching the target output DataFrame
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))

    processor = ICPEAnnualItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    processor._preprocess_data()

    preprocessed_df = processor.preprocessed_df

    expected_output = pl.DataFrame(
        {
            "day_of_processing": [
                datetime(2023, 1, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 2, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 3, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 4, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 5, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 6, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 7, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 8, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 9, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
            ],
            "processed_quantity": [10, 20, 15, 0, 5, 0, 25, 30, 0],
            "quantity_cumsum": [10, 30, 45, 45, 50, 50, 75, 105, 105],
        }
    )

    assert_frame_equal(preprocessed_df, expected_output)


def test_only_one_data_point(sample_icpe_data):
    """
    GIVE a single data point for ICPE item daily data
    WHEN the _preprocess_data method is called on ICPEAnnualItemProcessor with only one row of data
    THEN the resulting preprocessed_df should return a DataFrame with this single entry and correct cumulative sum
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    data = sample_icpe_data.head(1)

    processor = ICPEAnnualItemProcessor(icpe_item_daily_data=data, data_date_interval=data_date_interval)
    processor._preprocess_data()

    preprocessed_df = processor.preprocessed_df

    expected_output = pl.DataFrame(
        {
            "day_of_processing": [datetime(2023, 1, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris"))],
            "processed_quantity": [
                10,
            ],
            "quantity_cumsum": [
                10,
            ],
        }
    )

    assert_frame_equal(preprocessed_df, expected_output)


def test_empty_icpe_data():
    """
    GIVEN an empty ICPE item daily data DataFrame or None
    WHEN the _preprocess_data and _check_data_empty methods are called on ICPEAnnualItemProcessor
    THEN _check_data_empty should return True, indicating no meaningful data is present
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEAnnualItemProcessor(
        icpe_item_daily_data=pl.LazyFrame(
            {
                "day_of_processing": [],
                "processed_quantity": [],
                "authorized_quantity": [],
                "target_quantity": [],
            },
            schema={
                "day_of_processing": pl.Datetime(time_zone="Europe/Paris"),
                "processed_quantity": pl.Float64,
                "authorized_quantity": pl.Float64,
                "target_quantity": pl.Float64,
            },
        ),
        data_date_interval=data_date_interval,
    )

    processor._preprocess_data()

    assert processor._check_data_empty(), "Data should be considered empty when input DataFrame is empty."

    processor = ICPEAnnualItemProcessor(icpe_item_daily_data=None, data_date_interval=data_date_interval)

    processor._preprocess_data()

    assert processor._check_data_empty(), "Data should be considered empty when input DataFrame is None."


def test_correct_figure_creation(sample_icpe_data):
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEAnnualItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    processor._preprocess_data()
    processor._create_figure()

    figure = processor.figure

    assert isinstance(figure, go.Figure), "The generated figure should be a Plotly Figure object."
    assert len(figure.data) > 0, "Figure should contain at least one trace."


def test_process_build(sample_icpe_data):
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEAnnualItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    result = processor.build()

    assert isinstance(result, str), "Build method should return a JSON string representation of the figure."
    assert len(result) > 0, "Build result should not be empty."


def test_missing_columns():
    data = {"day_of_processing": [datetime(2023, 1, 1, tzinfo=tz)], "processed_quantity": [10]}

    icpe_data_df = pl.DataFrame(data).lazy()

    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEAnnualItemProcessor(icpe_item_daily_data=icpe_data_df, data_date_interval=data_date_interval)

    # Should raise a KeyError
    with pytest.raises(ColumnNotFoundError):
        processor._preprocess_data()


def test_incorrect_data_format():
    data = {
        "day_of_processing": ["Not a datetime"],  # Incorrect date format
        "processed_quantity": [10],
        "authorized_quantity": [50],
    }

    icpe_data_df = pl.LazyFrame(data)

    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEAnnualItemProcessor(icpe_item_daily_data=icpe_data_df, data_date_interval=data_date_interval)

    # Should raise a TypeError due to type column not being Timestamp
    with pytest.raises(InvalidOperationError):
        processor._preprocess_data()


def test_zero_processed_quantities():
    data = {
        "day_of_processing": [
            datetime(2023, 1, 1, tzinfo=tz),
            datetime(2023, 1, 2, tzinfo=tz),
            datetime(2023, 1, 3, tzinfo=tz),
        ],
        "processed_quantity": [0, 0, 0],
        "authorized_quantity": [50, 50, 50],
        "target_quantity": [25, 25, 25],
    }

    icpe_data_df = pl.LazyFrame(data)

    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEAnnualItemProcessor(icpe_item_daily_data=icpe_data_df, data_date_interval=data_date_interval)

    processor._preprocess_data()

    assert processor._check_data_empty(), (
        "Data should be considered empty when all rows have zero processed quantities."
    )


def test_only_nan_processed_quantities():
    data = {
        "day_of_processing": [
            datetime(2023, 1, 1, tzinfo=tz),
            datetime(2023, 1, 2, tzinfo=tz),
            datetime(2023, 1, 3, tzinfo=tz),
        ],
        "processed_quantity": [None, None, None],
        "authorized_quantity": [50, 50, 50],
        "target_quantity": [25, 25, 25],
    }

    icpe_data_df = pl.LazyFrame(data)

    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEAnnualItemProcessor(icpe_item_daily_data=icpe_data_df, data_date_interval=data_date_interval)

    processor._preprocess_data()

    assert processor._check_data_empty(), "Data should be considered empty when all processed quantities are NaN."
