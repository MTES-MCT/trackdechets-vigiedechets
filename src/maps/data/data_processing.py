"""
Data gathering and processing
"""

import logging
from datetime import datetime
from typing import Tuple

import polars as pl

from maps.data.figures_factory import create_icpe_graph

from ..constants import DAILY_ICPE_RUBRIQUES, ICPE_RUBRIQUES

logger = logging.getLogger(__name__)


def create_icpe_installations_df(
    df_installations: pl.DataFrame,
    df_installations_waste_processed: pl.DataFrame,
    date_interval: Tuple[datetime, datetime] | None = None,
) -> pl.DataFrame:
    logger.info("Creating installations DataFrame.")
    df_list = []
    for rubrique in ICPE_RUBRIQUES:
        logger.info(f"Creating installations DataFrame for rubrique {rubrique}")
        df_installations_filtered = df_installations.filter(pl.col("rubrique").str.contains(rubrique))

        if len(df_installations_filtered) == 0:
            continue

        df_installations_filtered = df_installations_filtered.group_by("code_aiot").agg(
            pl.col("siret").max(),
            pl.when(pl.col("quantite_autorisee").is_null().all())
            .then(None)
            .otherwise(pl.col("quantite_autorisee").sum())
            .alias("quantite_autorisee"),
            pl.col("latitude").max(),
            pl.col("longitude").max(),
            pl.col("raison_sociale").max(),
            pl.col("unite").max(),
            pl.col("adresse1").max(),
            pl.col("adresse2").max(),
            pl.col("code_postal").max(),
            pl.col("commune").max(),
        )

        df_waste_processed_filtered = df_installations_waste_processed.filter(
            pl.col("rubrique").str.contains(rubrique)
            & (pl.col("day_of_processing").is_between(*date_interval, closed="left"))
        )

        if len(df_waste_processed_filtered) == 0:
            continue


        # Compute daily or annual consumption rate
        daily_consumption_rate_expr = (
            pl.col("moyenne_quantite_journaliere_traitee") / pl.col("quantite_autorisee")
        ).alias("taux_consommation")
        annual_consumption_rate_expr = (pl.col("cumul_quantite_traitee") / pl.col("quantite_autorisee")).alias(
            "taux_consommation"
        )
        consumption_rate_expr = (
            daily_consumption_rate_expr if rubrique in DAILY_ICPE_RUBRIQUES else annual_consumption_rate_expr
        )

        df_stats = df_waste_processed_filtered.group_by("code_aiot").agg(
            pl.col("quantite_traitee").sum().alias("cumul_quantite_traitee").fill_null(0),
            pl.col("quantite_traitee").mean().alias("moyenne_quantite_journaliere_traitee").fill_null(0),
        )

        df_graphs = (
            df_waste_processed_filtered.filter(pl.col("day_of_processing").is_not_null())
            .sort(pl.col("day_of_processing"))
            .group_by("code_aiot")
            .map_groups(lambda x: create_icpe_graph(x, "code_aiot", rubrique))
        )

        df_installations_final = df_installations_filtered.join(
            df_stats, on="code_aiot", how="left", validate="1:1"
        ).join(df_graphs, on="code_aiot", how="left", validate="1:1")

        df_installations_final = df_installations_final.with_columns(
            pl.lit(rubrique).alias("rubrique"), pl.lit(date_interval[0].year).alias("year"), consumption_rate_expr
        )

        df_list.append(df_installations_final)

    gdf_final = pl.concat(df_list, how="diagonal")
    logger.info("Installations DataFrame created.")
    return gdf_final


def create_icpe_regional_df(
    df_regional_waste_processed: pl.DataFrame,
    regional_key_column: str | None = None,
    date_interval: Tuple[datetime, datetime] | None = None,
) -> pl.DataFrame:
    """
    Function to create regional DataFrame for ICPE.
    The DataFrame is aggregated as regional level ("region" or "departement") if `regional_key_column` is provided.
    If `regional_key_column` is None, then the dataframe is computed for all of France;

    Parameters
    ----------
    df_regional_waste_processed : polars.DataFrame
        The DataFrame containing regional waste processed data.
    regional_key_column : str or None, optional
        The column name to be used as the key for regional grouping. If None, no grouping is performed (country-wide processing).
    date_interval : tuple or None, optional
        The date interval for filtering data. If None, no filtering is performed.

    Returns
    -------
    polars.DataFrame
        The DataFrame after processing with additional columns for mean daily waste processed,
        rate of consumption, authorized quantity, number of installations and plotly graph.
    """
    logger.info("Creating regional DataFrame.")
    df_list = []
    for rubrique in ICPE_RUBRIQUES:
        df_waste_processed_filtered = df_regional_waste_processed.filter(
            pl.col("rubrique").str.contains(rubrique)
            & (pl.col("day_of_processing").is_between(*date_interval, closed="left"))
        )

        if len(df_waste_processed_filtered) == 0:
            continue

        if regional_key_column is not None:
            df_waste_processed_filtered = df_waste_processed_filtered.with_columns(
                pl.col(regional_key_column).cast(pl.String)
            )

        # Compute daily or annual consumption rate
        daily_consumption_rate_expr = (
            pl.col("moyenne_quantite_journaliere_traitee") / pl.col("quantite_autorisee")
        ).alias("taux_consommation")
        annual_consumption_rate_expr = (pl.col("cumul_quantite_traitee") / pl.col("quantite_autorisee")).alias(
            "taux_consommation"
        )

        consumption_rate_expr = (
            daily_consumption_rate_expr if rubrique in DAILY_ICPE_RUBRIQUES else annual_consumption_rate_expr
        )

        if regional_key_column is None:
            annual_stats = df_waste_processed_filtered.group_by("rubrique").agg(
                pl.col("quantite_traitee").mean().alias("moyenne_quantite_journaliere_traitee").fill_null(0),
                pl.col("quantite_traitee").sum().alias("cumul_quantite_traitee").fill_null(0),
                pl.col("quantite_autorisee").max(),
                pl.col("nombre_installations").max(),
            )
            annual_stats = annual_stats.with_columns(consumption_rate_expr)
            df = annual_stats
            df = df.with_columns(
                pl.lit(create_icpe_graph(df_waste_processed_filtered, key_column=None, rubrique=rubrique)).alias(
                    "graph"
                ),
                pl.lit(rubrique).alias("rubrique"),
                pl.lit(date_interval[0].year).alias("year"),
            )
        else:
            layer_name = "nom_departement"
            if regional_key_column == "code_region_insee":
                layer_name = "nom_region"

            annual_stats = (
                df_waste_processed_filtered.group_by(regional_key_column)
                .agg(
                    pl.col("quantite_traitee").mean().alias("moyenne_quantite_journaliere_traitee").fill_null(0),
                    pl.col("quantite_traitee").sum().alias("cumul_quantite_traitee").fill_null(0),
                    pl.col("quantite_autorisee").max(),
                    pl.col("nombre_installations").max(),
                    pl.col(layer_name).max(),
                )
                .with_columns(consumption_rate_expr)
            )

            # Create plotly graphs adding to daily waste processed the authorized quantity for each departement/region
            df_graphs = (
                df_waste_processed_filtered.filter(pl.col("day_of_processing").is_not_null())
                .sort(pl.col("day_of_processing"))
                .group_by(regional_key_column)
                .map_groups(lambda x: create_icpe_graph(x, key_column=regional_key_column, rubrique=rubrique))
            )

            df = annual_stats.join(df_graphs, on=regional_key_column, how="outer_coalesce", validate="1:1")
            df = df.with_columns(pl.lit(rubrique).alias("rubrique"), pl.lit(date_interval[0].year).alias("year"))
        df_list.append(df)

    df_concat = pl.concat(df_list, how="diagonal")

    if regional_key_column:
        df_concat = df_concat.filter(pl.col(regional_key_column).is_not_null())

    return df_concat
