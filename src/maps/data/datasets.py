"""This module contains the raw datasets.
The datasets are loaded in memory to be reusable by other functions.
"""

from dataclasses import dataclass

import polars as pl

from .data_extract import extract_dataset
from .queries import (
    icpe_departements_waste_processed_sql,
    icpe_france_waste_processed_sql,
    icpe_installations_sql,
    icpe_installations_waste_processed_sql,
    icpe_regions_waste_processed_sql,
    icpe_installations_schema_overrides,
    icpe_installations_waste_processed_schema_overrides,
    icpe_departements_waste_processed_schema_overrides,
    icpe_regions_waste_processed_schema_overrides,
    icpe_france_waste_processed_schema_overrides,
)


@dataclass
class Computed:
    icpe_installations_data: pl.DataFrame
    icpe_installations_waste_processed_data: pl.DataFrame
    icpe_departements_waste_processed_data: pl.DataFrame
    icpe_regions_waste_processed_data: pl.DataFrame
    icpe_france_waste_processed_data: pl.DataFrame


def get_data_df():
    icpe_installations_data = extract_dataset(icpe_installations_sql, icpe_installations_schema_overrides)
    icpe_installations_waste_processed_data = extract_dataset(
        icpe_installations_waste_processed_sql, icpe_installations_waste_processed_schema_overrides
    )
    icpe_departements_waste_processed_data = extract_dataset(
        icpe_departements_waste_processed_sql, icpe_departements_waste_processed_schema_overrides
    )
    icpe_regions_waste_processed_data = extract_dataset(
        icpe_regions_waste_processed_sql, icpe_regions_waste_processed_schema_overrides
    )
    icpe_france_waste_processed_data = extract_dataset(
        icpe_france_waste_processed_sql, icpe_france_waste_processed_schema_overrides
    )

    data = Computed(
        icpe_installations_data=icpe_installations_data,
        icpe_installations_waste_processed_data=icpe_installations_waste_processed_data,
        icpe_departements_waste_processed_data=icpe_departements_waste_processed_data,
        icpe_regions_waste_processed_data=icpe_regions_waste_processed_data,
        icpe_france_waste_processed_data=icpe_france_waste_processed_data,
    )
    return data
