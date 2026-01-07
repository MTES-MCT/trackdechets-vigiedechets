from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from ..graph_processors.html_components import LinkedCompaniesProcessor

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_linked_companies_data():
    return pl.LazyFrame(
        {
            "siret": ["12345678900011", "12345678900022", "12345678900033"],
            "name": ["Company A", "Company B", "Company C"],
            "address": ["1 Rue A", "2 Rue B", "3 Rue C"],
            "created_at": [
                datetime(2020, 1, 1, tzinfo=tz),
                datetime(2021, 6, 15, tzinfo=tz),
                datetime(2022, 12, 20, tzinfo=tz),
            ],
        }
    )


def test_linked_companies_processor_excludes_self_siret(sample_linked_companies_data):
    """
    GIVEN: Company with linked companies (same SIREN).
    WHEN: Building linked companies context.
    THEN: Returns list excluding the company's own SIRET, sorted by created_at.
    """
    processor = LinkedCompaniesProcessor(
        company_siret="12345678900011",
        linked_companies_data=sample_linked_companies_data,
    )

    result = processor.build()

    assert "siren" in result
    assert result["siren"] == "123456789"
    assert "siret_list" in result
    assert len(result["siret_list"]) == 2

    # Check self SIRET is excluded
    sirets_in_result = [item["siret"] for item in result["siret_list"]]
    assert "12345678900011" not in sirets_in_result
    assert "12345678900022" in sirets_in_result
    assert "12345678900033" in sirets_in_result

    # Check sorted by created_at
    assert result["siret_list"][0]["siret"] == "12345678900022"
    assert result["siret_list"][1]["siret"] == "12345678900033"


def test_linked_companies_processor_returns_empty_when_only_self_siret():
    """
    GIVEN: Linked companies data containing only the company's own SIRET.
    WHEN: Building linked companies context.
    THEN: Returns empty dict.
    """
    linked_companies_data = pl.LazyFrame(
        {
            "siret": ["12345678900011"],
            "name": ["Company A"],
            "address": ["1 Rue A"],
            "created_at": [datetime(2020, 1, 1, tzinfo=tz)],
        }
    )

    processor = LinkedCompaniesProcessor(
        company_siret="12345678900011",
        linked_companies_data=linked_companies_data,
    )

    result = processor.build()

    assert result == {}


def test_linked_companies_processor_returns_empty_when_no_data():
    """
    GIVEN: No linked companies data.
    WHEN: Building linked companies context.
    THEN: Returns empty dict.
    """
    processor = LinkedCompaniesProcessor(
        company_siret="12345678900011",
        linked_companies_data=None,
    )

    result = processor.build()

    assert result == {}
