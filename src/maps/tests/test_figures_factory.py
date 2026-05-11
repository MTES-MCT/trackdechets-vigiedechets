"""Tests for maps/data/figures_factory.py - create_icpe_graph function."""

import json
from datetime import date

import polars as pl

from maps.data.figures_factory import create_icpe_graph

ANNUAL_RUBRIQUE = "2760-1"
DAILY_RUBRIQUE = "2790"


def _make_df(dates, quantities, authorized=1000.0, with_objectif=False, objectif=500.0):
    data = {
        "day_of_processing": dates,
        "quantite_traitee": quantities,
        "quantite_autorisee": [authorized] * len(dates),
    }
    schema = {
        "day_of_processing": pl.Date,
        "quantite_traitee": pl.Float64,
        "quantite_autorisee": pl.Float64,
    }
    if with_objectif:
        data["quantite_objectif"] = [objectif] * len(dates)
        schema["quantite_objectif"] = pl.Float64
    return pl.DataFrame(data, schema=schema)


def test_create_icpe_graph_annual_returns_main_and_none_cumul():
    df = _make_df([date(2023, 1, 15), date(2023, 3, 20)], [100.0, 200.0])
    main_json, cumul_json = create_icpe_graph(df, key_column=None, rubrique=ANNUAL_RUBRIQUE)

    assert main_json is not None
    assert cumul_json is None
    parsed = json.loads(main_json)
    assert "data" in parsed
    assert "layout" in parsed


def test_create_icpe_graph_daily_returns_two_figures():
    df = _make_df([date(2023, 1, 15), date(2023, 1, 16)], [5.0, 8.0])
    main_json, cumul_json = create_icpe_graph(df, key_column=None, rubrique=DAILY_RUBRIQUE)

    assert main_json is not None
    assert cumul_json is not None
    # Both must be valid JSON
    json.loads(main_json)
    json.loads(cumul_json)


def test_create_icpe_graph_empty_data_no_key_column():
    df = pl.DataFrame(
        {
            "day_of_processing": pl.Series([None], dtype=pl.Date),
            "quantite_traitee": pl.Series([None], dtype=pl.Float64),
            "quantite_autorisee": pl.Series([1000.0]),
        }
    )
    result = create_icpe_graph(df, key_column=None, rubrique=ANNUAL_RUBRIQUE)
    assert result == (None, None)


def test_create_icpe_graph_with_key_column_annual():
    df = _make_df([date(2023, 1, 15), date(2023, 3, 20)], [100.0, 200.0])
    df = df.with_columns(pl.lit("INST001").alias("code_aiot"))

    result = create_icpe_graph(df, key_column="code_aiot", rubrique=ANNUAL_RUBRIQUE)

    assert isinstance(result, pl.DataFrame)
    assert "graph" in result.columns
    assert "graph_cumul" in result.columns
    assert result["graph"][0] is not None
    # Annual: cumulative trace is in the main figure; no separate cumul figure
    assert result["graph_cumul"][0] is None


def test_create_icpe_graph_with_key_column_daily():
    df = _make_df([date(2023, 1, 15), date(2023, 1, 16)], [5.0, 8.0])
    df = df.with_columns(pl.lit("INST001").alias("code_aiot"))

    result = create_icpe_graph(df, key_column="code_aiot", rubrique=DAILY_RUBRIQUE)

    assert isinstance(result, pl.DataFrame)
    assert result["graph"][0] is not None
    assert result["graph_cumul"][0] is not None


def test_create_icpe_graph_with_key_column_empty_data():
    df = pl.DataFrame(
        {
            "day_of_processing": pl.Series([None], dtype=pl.Date),
            "quantite_traitee": pl.Series([None], dtype=pl.Float64),
            "quantite_autorisee": pl.Series([1000.0]),
            "code_aiot": pl.Series(["INST001"]),
        }
    )
    result = create_icpe_graph(df, key_column="code_aiot", rubrique=ANNUAL_RUBRIQUE)

    assert isinstance(result, pl.DataFrame)
    assert result["graph"][0] is None
    assert result["graph_cumul"][0] is None
