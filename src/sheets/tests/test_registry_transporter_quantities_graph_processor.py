from datetime import datetime
from zoneinfo import ZoneInfo

import plotly.graph_objects as go
import polars as pl
import pytest

from ..graph_processors.plotly_components import RegistryTransporterQuantitiesGraphProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_registry_data():
    """Fixture for sample registry data."""
    return {
        "ndw_incoming": pl.LazyFrame(
            {
                "id": [1, 2, 3],
                "reception_date": [
                    datetime(2024, 1, 10, tzinfo=tz),
                    datetime(2024, 2, 15, tzinfo=tz),
                    datetime(2024, 2, 20, tzinfo=tz),
                ],
                "transporters_org_ids": [
                    ["12345678901234"],
                    ["12345678901234", "99999999999999"],
                    ["12345678901234"],
                ],
                "weight_value": [25.0, 12.0, None],
                "volume": [None, None, 9.7],
            }
        ),
        "ndw_outgoing": pl.LazyFrame(
            {
                "id": [4, 5],
                "dispatch_date": [
                    datetime(2024, 1, 20, tzinfo=tz),
                    datetime(2024, 3, 10, tzinfo=tz),
                ],
                "transporters_org_ids": [
                    ["12345678901234"],
                    ["12345678901234"],
                ],
                "weight_value": [30.0, None],
                "volume": [None, 15.5],
            }
        ),
        "excavated_land_incoming": pl.LazyFrame(
            {
                "id": [6, 7],
                "reception_date": [
                    datetime(2024, 2, 5, tzinfo=tz),
                    datetime(2024, 3, 15, tzinfo=tz),
                ],
                "transporters_org_ids": [
                    ["99999999999999"],
                    ["12345678901234"],
                ],
                "weight_value": [None, 8.0],
                "volume": [20.0, None],
            }
        ),
        "excavated_land_outgoing": pl.LazyFrame(
            {
                "id": [8],
                "dispatch_date": [datetime(2024, 3, 20, tzinfo=tz)],
                "transporters_org_ids": [["12345678901234"]],
                "weight_value": [40.0],
                "volume": [None],
            }
        ),
    }


@pytest.fixture
def date_interval():
    """Fixture for the date interval."""
    return (datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 3, 31, tzinfo=tz))


def test_preprocess_data(sample_registry_data, date_interval):
    """
    GIVEN registry data with transporter statements for multiple registry types
    WHEN _preprocess_data is called on RegistryTransporterQuantitiesGraphProcessor
    THEN the processor correctly groups quantities by registry type, date, and unit (weight/volume)
    """
    processor = RegistryTransporterQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_data=sample_registry_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_data()

    # Check that stats are populated for registry types with data
    assert processor.transported_quantities_stats["ndw_incoming"]["weight_value"] is not None
    assert processor.transported_quantities_stats["ndw_incoming"]["volume"] is not None
    assert processor.transported_quantities_stats["ndw_outgoing"]["weight_value"] is not None
    assert processor.transported_quantities_stats["ndw_outgoing"]["volume"] is not None
    assert processor.transported_quantities_stats["excavated_land_incoming"]["volume"] is None
    assert processor.transported_quantities_stats["excavated_land_incoming"]["weight_value"] is not None
    assert processor.transported_quantities_stats["excavated_land_outgoing"]["weight_value"] is not None

    # Check ndw_incoming weight quantities
    ndw_incoming_weight = processor.transported_quantities_stats["ndw_incoming"]["weight_value"]
    assert len(ndw_incoming_weight) == 2  # 2 different months
    assert ndw_incoming_weight["weight_value"].sum() == pytest.approx(37.0, rel=1e-6)  # 25.0 + 12.0


def test_preprocess_data_with_multiple_units(sample_registry_data, date_interval):
    """
    GIVEN registry data with both weight_value and volume
    WHEN _preprocess_data is called on RegistryTransporterQuantitiesGraphProcessor
    THEN the processor correctly processes both units separately
    """
    processor = RegistryTransporterQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_data=sample_registry_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_data()

    # Check that both weight and volume are processed for ndw_incoming
    ndw_incoming_weight = processor.transported_quantities_stats["ndw_incoming"]["weight_value"]
    ndw_incoming_volume = processor.transported_quantities_stats["ndw_incoming"]["volume"]

    assert ndw_incoming_weight is not None
    assert ndw_incoming_volume is not None
    assert len(ndw_incoming_volume) == 1  # 1 month with volume data
    assert ndw_incoming_volume["volume"].sum() == pytest.approx(9.7, rel=1e-6)


def test_check_data_empty(sample_registry_data, date_interval):
    """
    GIVEN registry data with matching company SIRET
    WHEN _check_data_empty is called after preprocessing
    THEN it returns False indicating data is not empty
    """
    processor = RegistryTransporterQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_data=sample_registry_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_data()

    assert not processor._check_data_empty()


def test_check_data_empty_with_no_matching_data(date_interval):
    """
    GIVEN registry data with no matching company SIRET
    WHEN _check_data_empty is called after preprocessing
    THEN it returns True indicating data is empty
    """
    empty_registry_data = {
        "ndw_incoming": pl.LazyFrame(
            {
                "id": [1],
                "reception_date": [datetime(2024, 1, 10, tzinfo=tz)],
                "transporters_org_ids": [["99999999999999"]],
                "weight_value": [25.0],
                "volume": [None],
            }
        ),
        "ndw_outgoing": None,
        "excavated_land_incoming": None,
        "excavated_land_outgoing": None,
    }

    processor = RegistryTransporterQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_data=empty_registry_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_data()

    assert processor._check_data_empty()


def test_create_figure(sample_registry_data, date_interval):
    """
    GIVEN preprocessed registry quantities data
    WHEN _create_figure is called on RegistryTransporterQuantitiesGraphProcessor
    THEN it creates a valid Plotly Figure with line traces for weight and volume
    """
    processor = RegistryTransporterQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_data=sample_registry_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_data()
    processor._create_figure()

    assert processor.figure is not None
    assert isinstance(processor.figure, go.Figure)
    assert len(processor.figure.data) > 0  # At least one line trace


def test_build(sample_registry_data, date_interval):
    """
    GIVEN registry data with transporter quantities
    WHEN build is called on RegistryTransporterQuantitiesGraphProcessor
    THEN it returns a JSON string representation of the figure
    """
    processor = RegistryTransporterQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_data=sample_registry_data,
        data_date_interval=date_interval,
    )
    result = processor.build()

    assert isinstance(result, str)
    assert len(result) > 0
    assert "data" in result


def test_build_with_empty_data(date_interval):
    """
    GIVEN registry data with no matching company SIRET
    WHEN build is called on RegistryTransporterQuantitiesGraphProcessor
    THEN it returns an empty dict
    """
    empty_registry_data = {
        "ndw_incoming": None,
        "ndw_outgoing": None,
        "excavated_land_incoming": None,
        "excavated_land_outgoing": None,
    }

    processor = RegistryTransporterQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_data=empty_registry_data,
        data_date_interval=date_interval,
    )
    result = processor.build()

    assert result == {}


def test_all_registry_types(sample_registry_data, date_interval):
    """
    GIVEN registry data for all registry types (ndw_incoming, ndw_outgoing, excavated_land_incoming, excavated_land_outgoing)
    WHEN _preprocess_data is called on RegistryTransporterQuantitiesGraphProcessor
    THEN the processor correctly processes all registry types
    """
    processor = RegistryTransporterQuantitiesGraphProcessor(
        company_siret="12345678901234",
        registry_data=sample_registry_data,
        data_date_interval=date_interval,
    )
    processor._preprocess_data()

    # Verify all types are processed
    assert processor.transported_quantities_stats["ndw_incoming"]["weight_value"] is not None
    assert processor.transported_quantities_stats["ndw_outgoing"]["weight_value"] is not None
    assert processor.transported_quantities_stats["excavated_land_incoming"]["weight_value"] is not None
    assert processor.transported_quantities_stats["excavated_land_outgoing"]["weight_value"] is not None
