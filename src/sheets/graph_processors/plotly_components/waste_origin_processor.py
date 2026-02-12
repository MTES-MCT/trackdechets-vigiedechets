from datetime import datetime

import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str

from .waste_origin_base_processor import WasteOriginBaseProcessor


class WasteOriginProcessor(WasteOriginBaseProcessor):
    """Component with a bar figure representing the quantity of waste received by departements (TOP 10) for a waste type.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    waste_type: str
        The type of waste being processed (e.g., "dangerous", "non_dangerous", "amiante").
    bs_data_df: LazyFrame
        LazyFrame containing the bordereau data for the given waste type.
    departements_regions_df: LazyFrame
        Static data about regions and departements with their codes.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        waste_type: str,
        bs_data_df: pl.LazyFrame,
        departements_regions_df: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        super().__init__(
            company_siret,
            {waste_type: bs_data_df},
            departements_regions_df,
            data_date_interval,
        )
        self.waste_type = waste_type
        self.preprocessed_serie = None

    def _preprocess_data(self) -> None:
        if len(self.bs_data_dfs) == 0:
            return

        bs_data_df = self.bs_data_dfs[self.waste_type]

        if bs_data_df is None:
            return

        df = bs_data_df.filter(pl.col("received_at").is_between(*self.data_date_interval))

        # The postal code is extracted from the address field using a simple regex
        df = df.with_columns(
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
        df = df.join(
            self.departements_regions_df,
            left_on="code_dep",
            right_on="DEP",
            how="left",
            validate="m:1",
        )

        # We create the column `cp_formatted` that will hold the two first digit
        # (three in the case of DOM/TOM) of the postal code
        df = df.with_columns(
            pl.when(pl.col("code_dep").is_not_null())
            .then(
                pl.concat_str(
                    pl.col("LIBELLE"),
                    pl.lit(" ("),
                    pl.col("code_dep"),
                    pl.lit(")"),
                )
            )
            .otherwise(pl.lit("Origine inconnue"))  # We handle the case of failed postal code extraction
            .alias("cp_formatted")
        )

        # Handle quantity refused
        if "quantity_refused" in df.collect_schema().names():
            df = df.with_columns(
                (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                    "quantity_received"
                )
            )

        serie = (
            df.filter(pl.col("recipient_company_siret") == self.company_siret)
            .group_by("cp_formatted")
            .agg(pl.col("quantity_received").sum())
            .filter(pl.col("quantity_received") > 0)
            .with_columns(pl.col("quantity_received").rank(descending=True).alias("rank"))
            .with_columns(
                pl.when(pl.col("rank") <= 10)
                .then("cp_formatted")
                .otherwise(pl.lit("Autres origines"))
                .alias("cp_formatted")  # Only TOP 10 'departements' are kept
            )
            .group_by("cp_formatted")
            .agg(pl.col("quantity_received").sum().round(2))
            .sort("quantity_received", descending=True)
        )

        serie = serie.sort(
            pl.when(pl.col("cp_formatted") == "Autres origines")
            .then(-1)
            .otherwise(pl.col("quantity_received").rank(descending=False))
        )

        final_serie = serie.collect()

        if len(final_serie) > 0:
            self.preprocessed_serie = final_serie

    def _check_data_empty(self) -> bool:
        if (self.preprocessed_serie is None) or len(self.preprocessed_serie) == 0:
            return True

        return False

    def _create_figure(self) -> None:
        # The bar chart has invisible bar (at *_annot positions) that will hold the labels
        # Invisible bar is the bar with width 0 but with a label.

        serie = self.preprocessed_serie

        y_cats = [tup_e for e in serie["cp_formatted"] for tup_e in (e, e + "_annot")]
        values = [tup_e for e in serie["quantity_received"] for tup_e in (e, 0)]
        texts = [
            tup_e
            for row in serie.iter_rows(named=True)
            for tup_e in (
                "",
                f"<b>{format_number_str(row['quantity_received'], precision=2)}t</b> - {row['cp_formatted']}",
            )
        ]
        hovertexts = [
            tup_e
            for row in serie.iter_rows(named=True)
            for tup_e in (
                f"{row['cp_formatted']} - <b>{format_number_str(row['quantity_received'], precision=2)}t</b> reçues",
                "",
            )
        ]
        bar_trace = go.Bar(
            x=values,
            y=y_cats,
            orientation="h",
            text=texts,
            textfont_size=14,
            textposition="outside",
            width=[tup_e for e in values for tup_e in (0.7, 1)],
            hovertext=hovertexts,
            hoverinfo="text",
        )

        # num_items = len(serie)
        # fig_height = max(200, num_items * 50)

        fig = go.Figure([bar_trace])
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False, type="category")
        fig.update_layout(
            # height=fig_height,
            margin={"t": 10, "b": 0, "l": 0, "r": 0},
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        self.figure = fig
