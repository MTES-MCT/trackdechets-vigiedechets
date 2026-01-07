from datetime import datetime
from zoneinfo import ZoneInfo

import plotly.graph_objects as go
import polars as pl
import pytest
from polars.exceptions import ColumnNotFoundError, InvalidOperationError
from polars.testing import assert_frame_equal

from ..graph_processors.plotly_components import ICPEDailyItemProcessor

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
    }

    return pl.DataFrame(data).lazy()


def test_preprocess_data(sample_icpe_data):
    """
    GIVEN daily processed ICPE item data for multiple days between 2023-01-01 and 2023-01-10
    WHEN the _preprocess_data method is called on ICPEDailyItemProcessor with the data date interval (2023-01-01, 2023-01-09)
    THEN the resulting preprocessed_df contains sorted, grouped daily quantities and mean_quantity is calculated correctly
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))

    processor = ICPEDailyItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

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
        }
    )

    assert_frame_equal(preprocessed_df, expected_output)
    # Mean of [10, 20, 15, 0, 5, 0, 25, 30, 0] = 105/9 ≈ 11.67
    assert abs(processor.mean_quantity - 11.666666666666666) < 0.001
    assert processor.authorized_quantity == 50


def test_date_filtering(sample_icpe_data):
    """
    GIVEN daily processed ICPE item data spanning multiple days
    WHEN the _preprocess_data method is called with a date interval that excludes some dates
    THEN only data within the date interval should be included in the preprocessed_df
    """
    # Filter to only include dates from 2023-01-03 to 2023-01-07
    data_date_interval = (datetime(2023, 1, 3, tzinfo=tz), datetime(2023, 1, 7, tzinfo=tz))

    processor = ICPEDailyItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    processor._preprocess_data()

    preprocessed_df = processor.preprocessed_df

    expected_output = pl.DataFrame(
        {
            "day_of_processing": [
                datetime(2023, 1, 3, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 4, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 5, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 6, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
                datetime(2023, 1, 7, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris")),
            ],
            "processed_quantity": [15, 0, 5, 0, 25],
        }
    )

    assert_frame_equal(preprocessed_df, expected_output)
    # Mean of [15, 0, 5, 0, 25] = 45/5 = 9.0
    assert abs(processor.mean_quantity - 9.0) < 0.001


def test_date_filtering_boundary_dates(sample_icpe_data):
    """
    GIVEN daily processed ICPE item data
    WHEN the date interval uses boundary dates (closed="both")
    THEN boundary dates should be included in the filtered data
    """
    # Use exact boundary dates
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 10, tzinfo=tz))

    processor = ICPEDailyItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    processor._preprocess_data()

    # Should include all 10 days
    assert len(processor.preprocessed_df) == 10
    assert processor.preprocessed_df["day_of_processing"].min() == datetime(2023, 1, 1, 0, 0, tzinfo=tz)
    assert processor.preprocessed_df["day_of_processing"].max() == datetime(2023, 1, 10, 0, 0, tzinfo=tz)


def test_date_filtering_outside_range(sample_icpe_data):
    """
    GIVEN daily processed ICPE item data
    WHEN the date interval is completely outside the data range
    THEN the preprocessed_df should be empty
    """
    # Date interval after all data
    data_date_interval = (datetime(2023, 2, 1, tzinfo=tz), datetime(2023, 2, 10, tzinfo=tz))

    processor = ICPEDailyItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    processor._preprocess_data()

    assert processor._check_data_empty(), "Data should be empty when date interval is outside data range"
    assert processor.preprocessed_df is None or len(processor.preprocessed_df) == 0


def test_only_one_data_point(sample_icpe_data):
    """
    GIVEN a single data point for ICPE item daily data
    WHEN the _preprocess_data method is called on ICPEDailyItemProcessor with only one row of data
    THEN the resulting preprocessed_df should return a DataFrame with this single entry
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    data = sample_icpe_data.head(1)

    processor = ICPEDailyItemProcessor(icpe_item_daily_data=data, data_date_interval=data_date_interval)
    processor._preprocess_data()

    preprocessed_df = processor.preprocessed_df

    expected_output = pl.DataFrame(
        {
            "day_of_processing": [datetime(2023, 1, 1, 0, 0, tzinfo=ZoneInfo(key="Europe/Paris"))],
            "processed_quantity": [10],
        }
    )

    assert_frame_equal(preprocessed_df, expected_output)
    assert processor.mean_quantity == 10.0


def test_empty_icpe_data():
    """
    GIVEN an empty ICPE item daily data DataFrame or None
    WHEN the _preprocess_data and _check_data_empty methods are called on ICPEDailyItemProcessor
    THEN _check_data_empty should return True, indicating no meaningful data is present
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEDailyItemProcessor(
        icpe_item_daily_data=pl.LazyFrame(
            {
                "day_of_processing": [],
                "processed_quantity": [],
                "authorized_quantity": [],
            },
            schema={
                "day_of_processing": pl.Datetime(time_zone="Europe/Paris"),
                "processed_quantity": pl.Float64,
                "authorized_quantity": pl.Float64,
            },
        ),
        data_date_interval=data_date_interval,
    )

    processor._preprocess_data()

    assert processor._check_data_empty(), "Data should be considered empty when input DataFrame is empty."

    processor = ICPEDailyItemProcessor(icpe_item_daily_data=None, data_date_interval=data_date_interval)

    processor._preprocess_data()

    assert processor._check_data_empty(), "Data should be considered empty when input DataFrame is None."


def test_correct_figure_creation(sample_icpe_data):
    """
    GIVEN valid ICPE item daily data
    WHEN the _preprocess_data and _create_figure methods are called
    THEN a valid Plotly Figure object should be created with at least one trace
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEDailyItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    processor._preprocess_data()
    processor._create_figure()

    figure = processor.figure

    assert isinstance(figure, go.Figure), "The generated figure should be a Plotly Figure object."
    assert len(figure.data) > 0, "Figure should contain at least one trace."


def test_process_build(sample_icpe_data):
    """
    GIVEN valid ICPE item daily data
    WHEN the build method is called
    THEN it should return a JSON string representation of the figure when data is not empty
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEDailyItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    result = processor.build()

    assert isinstance(result, str), "Build method should return a JSON string representation of the figure."
    assert len(result) > 0, "Build result should not be empty."


def test_process_build_empty_data():
    """
    GIVEN empty or None ICPE item daily data
    WHEN the build method is called
    THEN it should return an empty dict when data is empty
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEDailyItemProcessor(icpe_item_daily_data=None, data_date_interval=data_date_interval)

    result = processor.build()

    assert result == {}, "Build method should return an empty dict when data is empty."


def test_missing_columns():
    """
    GIVEN ICPE item daily data missing required columns
    WHEN the _preprocess_data method is called
    THEN it should raise a ColumnNotFoundError
    """
    data = {"day_of_processing": [datetime(2023, 1, 1, tzinfo=tz)], "processed_quantity": [10]}

    icpe_data_df = pl.DataFrame(data).lazy()

    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEDailyItemProcessor(icpe_item_daily_data=icpe_data_df, data_date_interval=data_date_interval)

    # Should raise a ColumnNotFoundError for missing authorized_quantity
    with pytest.raises(ColumnNotFoundError):
        processor._preprocess_data()


def test_incorrect_data_format():
    """
    GIVEN ICPE item daily data with incorrect date format
    WHEN the _preprocess_data method is called
    THEN it should raise an InvalidOperationError
    """
    data = {
        "day_of_processing": ["Not a datetime"],  # Incorrect date format
        "processed_quantity": [10],
        "authorized_quantity": [50],
    }

    icpe_data_df = pl.LazyFrame(data)

    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEDailyItemProcessor(icpe_item_daily_data=icpe_data_df, data_date_interval=data_date_interval)

    # Should raise an InvalidOperationError due to type column not being Timestamp
    with pytest.raises(InvalidOperationError):
        processor._preprocess_data()


def test_zero_processed_quantities():
    """
    GIVEN ICPE item daily data with all zero processed quantities
    WHEN the _preprocess_data method is called
    THEN the preprocessed_df should contain the data (unlike annual processor, daily processor doesn't check for zeros)
    """
    data = {
        "day_of_processing": [
            datetime(2023, 1, 1, tzinfo=tz),
            datetime(2023, 1, 2, tzinfo=tz),
            datetime(2023, 1, 3, tzinfo=tz),
        ],
        "processed_quantity": [0, 0, 0],
        "authorized_quantity": [50, 50, 50],
    }

    icpe_data_df = pl.LazyFrame(data)

    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))
    processor = ICPEDailyItemProcessor(icpe_item_daily_data=icpe_data_df, data_date_interval=data_date_interval)

    processor._preprocess_data()

    # Daily processor doesn't check for zero quantities, so data should not be empty
    assert not processor._check_data_empty(), "Data should not be considered empty even with zero quantities."
    assert processor.mean_quantity == 0.0


def test_mean_quantity_calculation(sample_icpe_data):
    """
    GIVEN ICPE item daily data
    WHEN the _preprocess_data method is called
    THEN mean_quantity should be calculated correctly from filtered data
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 5, tzinfo=tz))

    processor = ICPEDailyItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    processor._preprocess_data()

    # Mean of [10, 20, 15, 0, 5] = 50/5 = 10.0
    assert abs(processor.mean_quantity - 10.0) < 0.001


def test_authorized_quantity_extraction(sample_icpe_data):
    """
    GIVEN ICPE item daily data with authorized_quantity
    WHEN the _preprocess_data method is called
    THEN authorized_quantity should be extracted as the maximum value
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))

    processor = ICPEDailyItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    processor._preprocess_data()

    assert processor.authorized_quantity == 50


def test_figure_with_authorized_quantity(sample_icpe_data):
    """
    GIVEN ICPE item daily data with authorized_quantity
    WHEN the _create_figure method is called
    THEN the figure should include a horizontal line and annotation for authorized quantity
    """
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))

    processor = ICPEDailyItemProcessor(icpe_item_daily_data=sample_icpe_data, data_date_interval=data_date_interval)

    processor._preprocess_data()
    processor._create_figure()

    figure = processor.figure

    # Check that figure has annotations (authorized quantity annotation is added)
    assert len(figure.layout.annotations) > 0, "Figure should include authorized quantity annotation."
    # Check that annotation text contains authorized quantity info
    annotation_texts = [ann.text for ann in figure.layout.annotations if ann.text]
    assert any("autorisée" in text or "50" in text for text in annotation_texts), (
        "Figure annotation should mention authorized quantity."
    )


def test_figure_without_authorized_quantity():
    """
    GIVEN ICPE item daily data without authorized_quantity
    WHEN the _create_figure method is called
    THEN the figure should be created without authorized quantity line
    """
    data = {
        "day_of_processing": [
            datetime(2023, 1, 1, tzinfo=tz),
            datetime(2023, 1, 2, tzinfo=tz),
        ],
        "processed_quantity": [10, 20],
        "authorized_quantity": [None, None],
    }

    icpe_data_df = pl.LazyFrame(data)
    data_date_interval = (datetime(2023, 1, 1, tzinfo=tz), datetime(2023, 1, 9, tzinfo=tz))

    processor = ICPEDailyItemProcessor(icpe_item_daily_data=icpe_data_df, data_date_interval=data_date_interval)

    processor._preprocess_data()
    processor._create_figure()

    assert processor.figure is not None, "Figure should be created even without authorized quantity."
