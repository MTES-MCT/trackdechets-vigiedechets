import json
from datetime import datetime
from typing import Dict

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str

from ...constants import BSFF
from .waste_origin_base_processor import WasteOriginBaseProcessor


class WasteOriginsMapProcessor(WasteOriginBaseProcessor):
    """Component with a bubble map figure representing the quantity of waste received by regions.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    departements_regions_df: LazyFrame
        Static data about regions and départements with their codes.
    regions_geodata: GeoDataFrame
        GeoDataFrame including regions geometries.
    data_date_interval: tuple
        Date interval to filter data.
    packagings_data: LazyFrame, optional
        For BSFF data, packagings dataset to be able to compute the quantities.
        Quantities are stored at packaging level for BSFF, not at bordereau level.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        departements_regions_df: pl.LazyFrame,
        regions_geodata: gpd.GeoDataFrame,
        data_date_interval: tuple[datetime, datetime],
        packagings_data: pl.LazyFrame | None = None,
    ) -> None:
        super().__init__(company_siret, bs_data_dfs, departements_regions_df, data_date_interval, packagings_data)
        self.regions_geodata = regions_geodata
        self.preprocessed_df = None

    def _preprocess_data(self) -> None:
        if len(self.bs_data_dfs) == 0:
            return

        # Work on a copy to avoid mutating shared dictionary
        local_bs_data_dfs = dict(self.bs_data_dfs)
        local_bs_data_dfs[BSFF] = self._process_bsff_data(
            packagings_data=self.packagings_data, bsff_df=local_bs_data_dfs.get(BSFF)
        )

        # Filter out None values (e.g., BSFF when packagings_data is None)
        dfs_to_concat = [
            df.filter(pl.col("received_at").is_between(*self.data_date_interval))
            for df in local_bs_data_dfs.values()
            if df is not None
        ]

        if len(dfs_to_concat) == 0:
            return

        concat_df = pl.concat(dfs_to_concat, how="diagonal")

        # The postal code is extracted from the address field using a simple regex
        concat_df = concat_df.with_columns(
            pl.col("emitter_company_address").str.extract(r"([0-9]{5})").alias("cp")
        ).with_columns(
            pl.when(pl.col("cp").cast(pl.Int32).is_between(20000, 20190))  # Corse
            .then(pl.lit("2A"))
            .when(pl.col("cp").cast(pl.Int32).is_between(20190, 21000, closed="none"))  # Corse
            .then(pl.lit("2B"))
            .when(pl.col("cp").cast(pl.Int32) > 97000)  # DROM-COM
            .then(pl.col("cp").str.head(3))
            .otherwise(pl.col("cp").str.head(2))  # Metropole
            .alias("code_dep")
        )

        # 'Bordereau' data is merged with INSEE geographical data
        concat_df = concat_df.join(
            self.departements_regions_df,
            left_on="code_dep",
            right_on="DEP",
            how="left",
            validate="m:1",
        )

        # Handle quantity refused
        if "quantity_refused" in concat_df.collect_schema().names():
            concat_df = concat_df.with_columns(
                (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                    "quantity_received"
                )
            )

        # The 'Region' label is kept after aggregation
        df_grouped = (
            (
                concat_df.filter(pl.col("recipient_company_siret") == self.company_siret)
                .group_by("LIBELLE_reg")
                .agg(pl.col("quantity_received").sum().fill_nan(0).fill_null(0), pl.col("REG").max())
            )
            .collect()
            .to_pandas()
        )

        final_df = pd.merge(self.regions_geodata, df_grouped, left_on="code", right_on="REG", how="left")

        self.preprocessed_df = final_df

    def _check_data_empty(self) -> bool:
        if (
            (self.preprocessed_df is None)
            or self.preprocessed_df["quantity_received"].isna().all()
            or (len(self.preprocessed_df) == 0)
            or (self.preprocessed_df["quantity_received"] == 0).all()
        ):
            return True

        return False

    def _create_figure(self) -> None:
        gdf = self.preprocessed_df
        geojson = json.loads(gdf.to_json())

        # The figure is built in two part.
        # The first trace holds the 'region' geometries.
        # This trace doesn't hold preprocessed data.
        trace = go.Choropleth(
            geojson=geojson,
            z=[0] * len(gdf["quantity_received"]),
            locations=gdf.index,
            locationmode="geojson-id",
            colorscale=["#F9F8F6", "#F9F8F6"],
            marker_line_color="#979797",
            hoverinfo="skip",
            showscale=False,
        )

        sizeref = 2.0 * max(gdf["quantity_received"]) / (12**2)

        gdf_nonzero = gdf[gdf["quantity_received"].fillna(0) != 0]

        # This second trace will holds the circles that will be drawn on the map.
        # It is build using preprocessed data (size are relative to the quantity received).
        trace_2 = go.Scattergeo(
            geojson=geojson,
            locations=gdf_nonzero.index,
            locationmode="geojson-id",
            lat=gdf_nonzero.geometry.centroid.y,
            lon=gdf_nonzero.geometry.centroid.x,
            marker_sizeref=sizeref,
            marker_size=gdf_nonzero["quantity_received"],
            marker_sizemin=3,
            mode="markers+text",
            hovertext=[
                f"{e.nom} - <b>{format_number_str(e.quantity_received, precision=2)}t</b>"
                for e in gdf_nonzero.itertuples()
            ],
            hoverinfo="text",
            marker_color="#518FFF",
        )

        fig = go.Figure([trace, trace_2])
        fig.update_layout(
            margin={"b": 0, "t": 0, "r": 0, "l": 0},
            showlegend=False,
            legend_bgcolor="rgba(0,0,0,0)",
            xaxis_fixedrange=True,
            yaxis_fixedrange=True,
            dragmode=False,
        )
        fig.update_geos(
            fitbounds="locations",
            visible=False,
            showframe=False,
            projection_type="mercator",
        )

        self.figure = fig
