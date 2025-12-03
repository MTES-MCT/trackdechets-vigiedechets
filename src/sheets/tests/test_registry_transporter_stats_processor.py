from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from ..graph_processors.html_components import RegistryTransporterStatsProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_rndts_data():
    # Sample RNDTS data for different cases
    return {
        "ndw_incoming": pl.LazyFrame(
            {
                "id": [1, 2, 3],
                "reception_date": [
                    datetime(2024, 8, 9, tzinfo=tz),
                    datetime(2024, 8, 10, tzinfo=tz),
                    datetime(2024, 8, 10, tzinfo=tz),
                ],
                "transporters_org_ids": [
                    ["12345678901234"],
                    ["23456789012345"],
                    ["12345678901234", "34567890123456"],
                ],
                "weight_value": [25.0, 12.0, None],
                "volume": [None, None, 9.7],
            }
        ),
        "ndw_outgoing": pl.LazyFrame(
            {
                "id": [3],
                "dispatch_date": [datetime(2024, 8, 11, tzinfo=tz)],
                "transporters_org_ids": [["12345678901234"]],
                "volume": [30.0],
                "weight_value": [None],
            },
            schema_overrides={"weight_value": pl.Float64},
        ),
        "excavated_land_incoming": pl.LazyFrame(
            {
                "id": [4, 5],
                "reception_date": [datetime(2024, 8, 12, tzinfo=tz), datetime(2024, 8, 13, tzinfo=tz)],
                "transporters_org_ids": [["34567890123456"], ["12345678901234"]],
                "weight_value": [None, 3.0],
                "volume": [12.6, None],
            }
        ),
        "excavated_land_outgoing": pl.LazyFrame(
            {
                "id": [6],
                "dispatch_date": [datetime(2024, 8, 14, tzinfo=tz)],
                "transporters_org_ids": [["12345678901234"]],
                "weight_value": [40.0],
                "volume": [None],
            },
            schema_overrides={"volume": pl.Float64},
        ),
    }


@pytest.fixture
def date_interval():
    return (datetime(2024, 8, 1, tzinfo=tz), datetime(2024, 8, 31, tzinfo=tz))


def test_initialization(sample_rndts_data, date_interval):
    processor = RegistryTransporterStatsProcessor(
        company_siret="12345678901234",
        registry_data=sample_rndts_data,
        data_date_interval=date_interval,
    )

    assert processor.company_siret == "12345678901234"
    assert processor.registry_data == sample_rndts_data
    assert processor.data_date_interval == date_interval
    assert isinstance(processor.transported_statements_stats, dict)
    assert "ndw_incoming" in processor.transported_statements_stats


def test_empty_data(sample_rndts_data, date_interval):
    empty_data = {
        "ndw_incoming": pl.LazyFrame(
            {
                "id": [],
                "reception_date": [],
                "transporters_org_ids": [],
                "weight_value": [],
                "volume": [],
            },
            schema={
                "id": pl.String,
                "reception_date": pl.Datetime(time_zone="Europe/Paris"),
                "transporters_org_ids": pl.List(inner=pl.String),
                "weight_value": pl.Float64,
                "volume": pl.Float64,
            },
        ),
        "ndw_outgoing": pl.LazyFrame(
            {
                "id": [],
                "dispatch_date": [],
                "transporters_org_ids": [],
                "weight_value": [],
                "volume": [],
            },
            schema={
                "id": pl.String,
                "dispatch_date": pl.Datetime(time_zone="Europe/Paris"),
                "transporters_org_ids": pl.List(inner=pl.String),
                "weight_value": pl.Float64,
                "volume": pl.Float64,
            },
        ),
        "excavated_land_incoming": pl.LazyFrame(
            {
                "id": [],
                "reception_date": [],
                "transporters_org_ids": [],
                "weight_value": [],
                "volume": [],
            },
            schema={
                "id": pl.String,
                "reception_date": pl.Datetime(time_zone="Europe/Paris"),
                "transporters_org_ids": pl.List(inner=pl.String),
                "weight_value": pl.Float64,
                "volume": pl.Float64,
            },
        ),
        "excavated_land_outgoing": pl.LazyFrame(
            {
                "id": [],
                "dispatch_date": [],
                "transporters_org_ids": [],
                "weight_value": [],
                "volume": [],
            },
            schema={
                "id": pl.String,
                "dispatch_date": pl.Datetime(time_zone="Europe/Paris"),
                "transporters_org_ids": pl.List(inner=pl.String),
                "weight_value": pl.Float64,
                "volume": pl.Float64,
            },
        ),
    }
    processor = RegistryTransporterStatsProcessor(
        company_siret="12345678901234",
        registry_data=empty_data,
        data_date_interval=date_interval,
    )

    empty_data = {
        "ndw_incoming": None,
        "ndw_outgoing": None,
        "excavated_land_incoming": None,
        "excavated_land_outgoing": None,
    }
    processor = RegistryTransporterStatsProcessor(
        company_siret="12345678901234",
        registry_data=empty_data,
        data_date_interval=date_interval,
    )

    # Test data not in date interval
    processor = RegistryTransporterStatsProcessor(
        company_siret="12345678901234",
        registry_data=sample_rndts_data,
        data_date_interval=(datetime(2023, 8, 1, tzinfo=tz), datetime(2024, 7, 30, tzinfo=tz)),
    )

    assert processor.build() == {
        "ndw_incoming": {"count": 0, "mass_quantity": "0", "volume_quantity": "0"},
        "ndw_outgoing": {"count": 0, "mass_quantity": "0", "volume_quantity": "0"},
        "excavated_land_incoming": {"count": 0, "mass_quantity": "0", "volume_quantity": "0"},
        "excavated_land_outgoing": {"count": 0, "mass_quantity": "0", "volume_quantity": "0"},
    }


def test_data_preprocessing(sample_rndts_data, date_interval):
    processor = RegistryTransporterStatsProcessor(
        company_siret="12345678901234",
        registry_data=sample_rndts_data,
        data_date_interval=date_interval,
    )

    processor._preprocess_bs_data()

    assert processor.transported_statements_stats["ndw_incoming"]["count"] == 2
    assert processor.transported_statements_stats["ndw_incoming"]["mass_quantity"] == "25"
    assert processor.transported_statements_stats["ndw_incoming"]["volume_quantity"] == "9.7"

    assert processor.transported_statements_stats["ndw_outgoing"]["count"] == 1
    assert processor.transported_statements_stats["ndw_outgoing"]["mass_quantity"] == "0"
    assert processor.transported_statements_stats["ndw_outgoing"]["volume_quantity"] == "30"

    assert processor.transported_statements_stats["excavated_land_incoming"]["count"] == 1
    assert processor.transported_statements_stats["excavated_land_incoming"]["mass_quantity"] == "3"
    assert processor.transported_statements_stats["excavated_land_incoming"]["volume_quantity"] == "0"

    assert processor.transported_statements_stats["excavated_land_outgoing"]["count"] == 1
    assert processor.transported_statements_stats["excavated_land_outgoing"]["mass_quantity"] == "40"
    assert processor.transported_statements_stats["excavated_land_outgoing"]["volume_quantity"] == "0"


def test_build_output(sample_rndts_data, date_interval):
    processor = RegistryTransporterStatsProcessor(
        company_siret="12345678901234",
        registry_data=sample_rndts_data,
        data_date_interval=date_interval,
    )

    result = processor.build()

    assert isinstance(result, dict)
    assert len(result) > 0

    assert "ndw_incoming" in result
    assert "mass_quantity" in result["ndw_incoming"]
    assert "volume_quantity" in result["ndw_incoming"]
    assert result["ndw_incoming"]["count"] == 2
    assert result["ndw_incoming"]["mass_quantity"] == "25"
    assert result["ndw_incoming"]["volume_quantity"] == "9.7"

    assert "ndw_outgoing" in result
    assert "mass_quantity" in result["ndw_outgoing"]
    assert "volume_quantity" in result["ndw_outgoing"]
    assert result["ndw_outgoing"]["count"] == 1
    assert result["ndw_outgoing"]["mass_quantity"] == "0"
    assert result["ndw_outgoing"]["volume_quantity"] == "30"

    assert "excavated_land_incoming" in result
    assert "mass_quantity" in result["excavated_land_incoming"]
    assert "volume_quantity" in result["excavated_land_incoming"]
    assert result["excavated_land_incoming"]["count"] == 1
    assert result["excavated_land_incoming"]["mass_quantity"] == "3"
    assert result["excavated_land_incoming"]["volume_quantity"] == "0"

    assert "excavated_land_outgoing" in result
    assert "mass_quantity" in result["excavated_land_outgoing"]
    assert "volume_quantity" in result["excavated_land_outgoing"]
    assert result["excavated_land_outgoing"]["count"] == 1
    assert result["excavated_land_outgoing"]["mass_quantity"] == "40"
    assert result["excavated_land_outgoing"]["volume_quantity"] == "0"
