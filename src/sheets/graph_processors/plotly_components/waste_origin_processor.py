from datetime import datetime

import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str


class WasteOriginProcessor:
    """Bar chart of top-10 waste origin departments for a given BSD type.

    Parameters
    ----------
    company_siret : str
        SIRET number of the establishment for which the data is displayed.
    waste_type : str
        One of "bsdd", "bsda", "texs", "dnd".
    data_df : pl.LazyFrame | None
        LazyFrame containing the data for the given waste type, or None if no data.
    departements_regions_df : pl.LazyFrame
        Static data about regions and departements with their codes.
    data_date_interval : tuple[datetime, datetime]
        Date interval to filter data.
    """

    BSD_TYPES = ("bsdd", "bsda")
    REGISTRY_TYPES = ("texs", "dnd")

    def __init__(
        self,
        company_siret: str,
        waste_type: str,
        data_df: pl.LazyFrame | None,
        departements_regions_df: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.waste_type = waste_type
        self.data_df = data_df
        self.departements_regions_df = departements_regions_df
        self.data_date_interval = data_date_interval

        self.preprocessed_serie = None
        self.figure = None

    def _preprocess_data(self) -> None:
        if self.data_df is None:
            return

        if self.waste_type in self.BSD_TYPES:
            df = self.data_df.with_columns(
                pl.col("received_at").alias("date"),
                pl.col("emitter_company_address").str.extract(r"([0-9]{5})").alias("cp"),
                pl.col("recipient_company_siret").alias("siret"),
                pl.col("quantity_received"),
            )
            if "quantity_refused" in df.collect_schema().names():
                df = df.with_columns(
                    (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                        "quantity_received"
                    )
                )
        else:  # REGISTRY_TYPES
            df = self.data_df.with_columns(
                pl.col("reception_date").alias("date"),
                pl.col("postal_code").alias("cp"),
                pl.col("siret"),
                pl.col("weight_value").alias("quantity_received"),
            )

        df = df.filter(pl.col("date").is_between(*self.data_date_interval))

        df = (
            df.with_columns(pl.col("cp").cast(pl.Int32, strict=False).alias("cp_int"))
            .with_columns(
                pl.when(pl.col("cp_int").is_null())
                .then(pl.lit(None))
                .when(pl.col("cp_int").is_between(20000, 20190))  # Corse-du-Sud
                .then(pl.lit("2A"))
                .when(pl.col("cp_int").is_between(20190, 21000, closed="none"))  # Haute-Corse
                .then(pl.lit("2B"))
                .when(pl.col("cp_int") > 97000)  # DROM-COM
                .then(pl.col("cp").str.head(3))
                .otherwise(pl.col("cp").str.head(2))  # Metropole
                .alias("code_dep")
            )
            .drop("cp_int")
        )

        df = df.join(
            self.departements_regions_df,
            left_on="code_dep",
            right_on="DEP",
            how="left",
            validate="m:1",
        )

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
            .otherwise(pl.lit("Origine inconnue"))
            .alias("cp_formatted")
        )

        serie = (
            df.filter(pl.col("siret") == self.company_siret)
            .group_by("cp_formatted")
            .agg(pl.col("quantity_received").sum())
            .filter(pl.col("quantity_received") > 0)
            .with_columns(pl.col("quantity_received").rank(descending=True).alias("rank"))
            .with_columns(
                pl.when(pl.col("rank") <= 10)
                .then("cp_formatted")
                .otherwise(pl.lit("Autres origines"))
                .alias("cp_formatted")
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

    def _create_figure(self) -> None:
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

        fig = go.Figure([bar_trace])
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False, type="category")
        fig.update_layout(
            margin={"t": 10, "b": 0, "l": 0, "r": 0},
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        self.figure = fig

    def build(self) -> dict | str:
        self._preprocess_data()
        if self.preprocessed_serie is None or len(self.preprocessed_serie) == 0:
            return {}
        self._create_figure()
        return self.figure.to_json()
