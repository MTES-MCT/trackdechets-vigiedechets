from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from ..graph_processors.plotly_components import RegistryStatementsGraphProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_data():
    incoming_data = pl.LazyFrame(
        {
            "id": [1, 2, 3, 4],
            "reception_date": [
                datetime(2024, 8, 9, tzinfo=tz),
                datetime(2024, 9, 10, tzinfo=tz),
                datetime(2024, 7, 15, tzinfo=tz),  # Not in data interval
                datetime(2024, 8, 15, tzinfo=tz),
            ],
            "siret": [
                "12345678901234",
                "12345678901234",
                "12345678901234",
                "98765432109876",
            ],
        }
    )

    outgoing_data = pl.LazyFrame(
        {
            "id": [4, 5, 6],
            "dispatch_date": [
                datetime(2024, 8, 11, tzinfo=tz),
                datetime(2024, 8, 12, tzinfo=tz),
                datetime(2024, 8, 1, tzinfo=tz),
            ],
            "siret": [
                "12345678901234",
                "12345678901234",
                "98765432109876",
            ],
        }
    )

    date_interval = (datetime(2024, 8, 1, tzinfo=tz), datetime(2024, 9, 30, tzinfo=tz))

    return incoming_data, outgoing_data, date_interval


def test_initialization(sample_data):
    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryStatementsGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        statement_type="non_dangerous_waste",
        data_date_interval=date_interval,
    )

    assert processor.company_siret == "12345678901234"
    assert processor.registry_incoming_data is incoming_data
    assert processor.registry_outgoing_data is outgoing_data
    assert processor.statement_type == "non_dangerous_waste"
    assert processor.data_date_interval == date_interval
    assert processor.statements_emitted_by_month_serie is None
    assert processor.statements_received_by_month_serie is None
    assert processor.figure is None


def test_preprocess_bs_data(sample_data):
    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryStatementsGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        statement_type="non_dangerous_waste",
        data_date_interval=date_interval,
    )

    processor._preprocess_bs_data()

    # Only two rows for each data set should be included in the series, as the others are either outside the date interval or have a different SIRET
    assert processor.statements_received_by_month_serie is not None
    assert processor.statements_received_by_month_serie.shape == (2, 2)
    assert processor.statements_received_by_month_serie["id"].sum() == 2
    assert processor.statements_emitted_by_month_serie is not None
    assert processor.statements_emitted_by_month_serie.shape == (1, 2)
    assert processor.statements_emitted_by_month_serie["id"].sum() == 2


def test_check_data_empty(sample_data):
    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryStatementsGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        statement_type="non_dangerous_waste",
        data_date_interval=date_interval,
    )

    processor._preprocess_bs_data()

    assert not processor._check_data_empty()

    processor = RegistryStatementsGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        statement_type="non_dangerous_waste",
        data_date_interval=(datetime(2023, 8, 1, tzinfo=tz), datetime(2024, 7, 1, tzinfo=tz)),
    )

    processor._preprocess_bs_data()

    assert processor._check_data_empty()


def test_create_figure(sample_data):
    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryStatementsGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        statement_type="non_dangerous_waste",
        data_date_interval=date_interval,
    )

    processor._preprocess_bs_data()
    processor._create_figure()

    assert processor.figure is not None


def test_build_output(sample_data):
    incoming_data, outgoing_data, date_interval = sample_data

    processor = RegistryStatementsGraphProcessor(
        company_siret="12345678901234",
        registry_incoming_data=incoming_data,
        registry_outgoing_data=outgoing_data,
        statement_type="non_dangerous_waste",
        data_date_interval=date_interval,
    )

    result = processor.build()

    assert isinstance(result, str)  # JSON string
    assert len(result) > 0
