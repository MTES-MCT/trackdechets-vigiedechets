import logging

import polars as pl

from maps.data.data_processing import create_icpe_installations_df, create_icpe_regional_df
from maps.models import DepartementsComputation, FranceComputation, InstallationsComputation, RegionsComputation
from maps.utils import get_data_date_interval_for_year

logger = logging.getLogger(__name__)


def build_stats_and_figs(year: int, clear_year: bool = False):
    logger.info(f"Building stats and figs for year {year}")
    existing_computations = [
        DepartementsComputation.objects.filter(year=year),
        InstallationsComputation.objects.filter(year=year),
        RegionsComputation.objects.filter(year=year),
        FranceComputation.objects.filter(year=year),
    ]
    if clear_year:
        for computation_o in existing_computations:
            computation_o.delete()

    date_interval = get_data_date_interval_for_year(year)

    icpe_installations_data = pl.read_parquet("temp_data/icpe_installations_data.parquet")
    icpe_installations_waste_processed_data = pl.read_parquet(
        "temp_data/icpe_installations_waste_processed_data.parquet"
    )
    icpe_departements_waste_processed_data = pl.read_parquet(
        "temp_data/icpe_departements_waste_processed_data.parquet"
    )
    icpe_regions_waste_processed_data = pl.read_parquet("temp_data/icpe_regions_waste_processed_data.parquet")
    icpe_france_waste_processed_data = pl.read_parquet("temp_data/icpe_france_waste_processed_data.parquet")

    icpe_installations_data = create_icpe_installations_df(
        icpe_installations_data, icpe_installations_waste_processed_data, date_interval
    )
    InstallationsComputation.objects.bulk_create(
        InstallationsComputation(**e) for e in icpe_installations_data.iter_rows(named=True)
    )

    icpe_regions_data = create_icpe_regional_df(
        icpe_regions_waste_processed_data,
        "code_region_insee",
        date_interval,
    )
    RegionsComputation.objects.bulk_create(RegionsComputation(**e) for e in icpe_regions_data.iter_rows(named=True))

    icpe_departements_data = create_icpe_regional_df(
        icpe_departements_waste_processed_data,
        "code_departement_insee",
        date_interval,
    )
    DepartementsComputation.objects.bulk_create(
        DepartementsComputation(**e) for e in icpe_departements_data.iter_rows(named=True)
    )

    icpe_france_data = create_icpe_regional_df(
        icpe_france_waste_processed_data,
        None,
        date_interval,
    )
    FranceComputation.objects.bulk_create(FranceComputation(**e) for e in icpe_france_data.iter_rows(named=True))
