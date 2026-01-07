import polars as pl
import pytest

from ..graph_processors.html_components import ICPEItemsProcessor


@pytest.fixture
def sample_icpe_data():
    return pl.LazyFrame(
        {
            "code_aiot": ["0001.00001", "0001.00002", "0001.00003"],
            "rubrique": ["2710", "2720", "2770"],
            "quantite": [1500.5, 2000.0, 3500.123],
            "unite": ["t/an", "t/an", "t/an"],
        }
    )


def test_icpe_items_processor_returns_sorted_items(sample_icpe_data):
    """
    GIVEN: Company with ICPE authorized items.
    WHEN: Building ICPE items context.
    THEN: Returns list of sorted items by rubrique with formatted quantities.
    """
    processor = ICPEItemsProcessor(
        company_siret="12345678900011",
        icpe_data=sample_icpe_data,
    )

    result = processor.build()

    assert isinstance(result, list)
    assert len(result) == 3

    # Check sorted by rubrique
    assert result[0]["rubrique"] == "2710"
    assert result[1]["rubrique"] == "2720"
    assert result[2]["rubrique"] == "2770"

    # Check quantity formatting
    assert result[0]["quantite"] == "1 500.5"
    assert result[1]["quantite"] == "2 000"


def test_icpe_items_processor_returns_empty_when_no_data():
    """
    GIVEN: Company with no ICPE data.
    WHEN: Building ICPE items context.
    THEN: Returns empty dict.
    """
    processor = ICPEItemsProcessor(
        company_siret="12345678900011",
        icpe_data=None,
    )

    result = processor.build()

    assert result == {}


def test_icpe_items_processor_handles_nan_quantities():
    """
    GIVEN: ICPE data with NaN quantite values.
    WHEN: Building ICPE items context.
    THEN: Converts "nan" strings to None for JSON compatibility.
    """
    icpe_data = pl.LazyFrame(
        {
            "code_aiot": ["0001.00001"],
            "rubrique": ["2710"],
            "quantite": [float("nan")],
            "unite": ["t/an"],
        }
    )

    processor = ICPEItemsProcessor(
        company_siret="12345678900011",
        icpe_data=icpe_data,
    )

    result = processor.build()

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["quantite"] is None

