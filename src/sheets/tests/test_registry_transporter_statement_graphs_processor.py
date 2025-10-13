from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from ..graph_processors.plotly_components_processors import RegistryTransporterStatementsStatsGraphProcessor

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
    processor = RegistryTransporterStatementsStatsGraphProcessor(
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
    processor = RegistryTransporterStatementsStatsGraphProcessor(
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
    processor = RegistryTransporterStatementsStatsGraphProcessor(
        company_siret="12345678901234",
        registry_data=empty_data,
        data_date_interval=date_interval,
    )

    # Test data not in date interval
    processor = RegistryTransporterStatementsStatsGraphProcessor(
        company_siret="12345678901234",
        registry_data=sample_rndts_data,
        data_date_interval=(datetime(2023, 8, 1, tzinfo=tz), datetime(2024, 7, 30, tzinfo=tz)),
    )

    assert processor.build() == {}


def test_data_preprocessing(sample_rndts_data, date_interval):
    processor = RegistryTransporterStatementsStatsGraphProcessor(
        company_siret="12345678901234",
        registry_data=sample_rndts_data,
        data_date_interval=date_interval,
    )

    processor._preprocess_data()

    assert processor.transported_statements_stats["ndw_incoming"]["number_statements"].item() == 2
    assert processor.transported_statements_stats["ndw_outgoing"]["number_statements"].item() == 1
    assert processor.transported_statements_stats["excavated_land_incoming"]["number_statements"].item() == 1
    assert processor.transported_statements_stats["excavated_land_outgoing"]["number_statements"].item() == 1


def test_figure_output(sample_rndts_data, date_interval):
    processor = RegistryTransporterStatementsStatsGraphProcessor(
        company_siret="12345678901234",
        registry_data=sample_rndts_data,
        data_date_interval=date_interval,
    )

    figure = processor.build()
    import json

    figure_dict = json.loads(figure)

    assert isinstance(figure_dict, dict)
    data = figure_dict["data"]

    assert all(record["text"] is not None and record["y"] == record["text"] for record in data)
