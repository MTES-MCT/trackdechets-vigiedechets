import json
import locale
from datetime import datetime, timedelta
from itertools import chain
from typing import Dict, Literal

import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str

from ..constants import BSDA, BSDASRI, BSDD, BSDD_NON_DANGEROUS, BSFF, BSVHU

# classes returning a serialized (json) plotly visualization to be consumed by a plotly script
locale.setlocale(locale.LC_ALL, "fr_FR")


class BsdQuantitiesGraph:
    """Component with a Line Figure showing incoming and outgoing quantities of waste.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data: LazyFrame
        LazyFrame containing data for a given 'bordereau' type.
    quantity_variables_names: list of str
        The names of the variables to use to compute quantity statistics. Several variables can be used.
    packagings_data : LazyFrame
        For BSFF data, packagings dataset to be able to compute the quantities.
    """

    def __init__(
        self,
        company_siret: str,
        bs_type: str,
        bs_data: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
        quantity_variables_names: list[str] = ["quantity_received"],
        packagings_data: pl.LazyFrame | None = None,
    ):
        self.bs_data = bs_data
        self.bs_type = bs_type
        self.packagings_data = packagings_data
        self.company_siret = company_siret
        self.data_date_interval = data_date_interval
        self.quantity_variables_names = self._validate_quantity_variables_names(
            quantity_variables_names, packagings_data
        )

        self.incoming_data_by_month_series = []
        self.outgoing_data_by_month_series = []

        self.figure = None

    @staticmethod
    def _validate_quantity_variables_names(quantity_variables_names, packagings_data):
        allowed_quantity_variables_names = [
            "quantity_received",
            "acceptation_weight",
            "volume",
        ]

        clean_quantity_variables_names = [e for e in quantity_variables_names if e in allowed_quantity_variables_names]

        # Allows to handle the case when there is no packagings data but there is BSFF data
        if packagings_data is None:
            clean_quantity_variables_names = [
                e if e != "acceptation_weight" else "quantity_received" for e in clean_quantity_variables_names
            ]

        return list(set(clean_quantity_variables_names))

    def _preprocess_data(self) -> None:
        bs_data = self.bs_data

        incoming_data = bs_data.filter(
            (pl.col("recipient_company_siret") == self.company_siret)
            & pl.col("received_at").is_between(*self.data_date_interval)
        )

        outgoing_data = bs_data.filter(
            (pl.col("emitter_company_siret") == self.company_siret)
            & pl.col("sent_at").is_between(*self.data_date_interval)
        )

        # Handle quantity refused
        if self.bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDASRI]:
            incoming_data = incoming_data.with_columns(
                (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0))
            )

            outgoing_data = outgoing_data.with_columns(
                (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0))
            )

        # We iterate over the different variables chosen to compute the statistics
        for variable_name in self.quantity_variables_names:
            # If there is a packagings_data LazyFrame, then it means that we are
            # computing BSFF statistics, in this case we use the packagings data instead of
            # 'bordereaux' data as quantity information is stored at packaging level

            if self.bs_type == BSFF:
                if self.packagings_data is None:
                    # Case when there is BSFFs but no packagings info
                    continue

                incoming_data_by_month = pl.DataFrame()
                outgoing_data_by_month = pl.DataFrame()

                incoming_data = incoming_data.join(
                    self.packagings_data.filter(pl.col("acceptation_date").is_not_null()),
                    left_on="id",
                    right_on="bsff_id",
                )
                incoming_data_by_month = incoming_data.group_by(
                    pl.col("acceptation_date").dt.truncate("1mo").alias("received_at")
                ).agg(pl.col(variable_name).sum().cast(pl.Float64))

                outgoing_data = outgoing_data.join(self.packagings_data, left_on="id", right_on="bsff_id")
                outgoing_data_by_month = outgoing_data.group_by(pl.col("sent_at").dt.truncate("1mo")).agg(
                    pl.col(variable_name).sum().cast(pl.Float64)
                )
            else:
                outgoing_data_by_month = outgoing_data.group_by(pl.col("sent_at").dt.truncate("1mo")).agg(
                    pl.col(variable_name).sum()
                )

                incoming_data_by_month = incoming_data.group_by(pl.col("received_at").dt.truncate("1mo")).agg(
                    pl.col(variable_name).sum()
                )

            self.incoming_data_by_month_series.append(incoming_data_by_month.sort("received_at").collect())
            self.outgoing_data_by_month_series.append(outgoing_data_by_month.sort("sent_at").collect())

    def _check_data_empty(self) -> bool:
        incoming_data_by_month_series = self.incoming_data_by_month_series
        outgoing_data_by_month_series = self.outgoing_data_by_month_series

        # If DataFrames are empty then output is empty
        if all(len(s) == len(z) == 0 for s, z in zip(incoming_data_by_month_series, outgoing_data_by_month_series)):
            return True

        return False

    def _create_figure(self) -> None:
        fig = go.Figure()

        lines = []  # Will store the lines graph objects

        # We store the minimum date of each series to be able to configure
        # the tick 0 of the figure
        mins_x = []

        # This is used to configure the dticks in case of low number of data points.
        numbers_of_data_points = []

        # We store the minimum date of each series to be able to configure
        # the tick 0 of y axis the figure
        maxs_y = []

        # We create two lines (for incoming and outgoing) for each quantity variable chosen
        for variable_name, incoming_data_by_month, outgoing_data_by_month in zip(
            self.quantity_variables_names,
            self.incoming_data_by_month_series,
            self.outgoing_data_by_month_series,
        ):
            incoming_line_name = "Quantité entrante"
            incoming_hover_text = "{} - <b>{}</b> tonnes entrantes"
            outgoing_line_name = "Quantité sortante"
            outgoing_hover_text = "{} - <b>{}</b> tonnes sortantes"
            marker_line_style = "solid"
            marker_symbol = "circle"
            marker_size = 6

            # To handle the case of volume
            if variable_name == "volume":
                incoming_line_name = "Volume entrant"
                incoming_hover_text = "{} - <b>{}</b> m³ entrants"
                outgoing_line_name = "Volume sortant"
                outgoing_hover_text = "{} - <b>{}</b> m³ sortants"
                marker_line_style = "dash"
                marker_symbol = "triangle-up"
                marker_size = 10

            if len(incoming_data_by_month) > 0:
                incoming_line = go.Scatter(
                    x=incoming_data_by_month["received_at"].to_list(),
                    y=incoming_data_by_month[variable_name].to_list(),
                    name=incoming_line_name,
                    mode="lines+markers",
                    hovertext=[
                        incoming_hover_text.format(index.strftime("%B %y").capitalize(), format_number_str(e))
                        for index, e in incoming_data_by_month.iter_rows()
                    ],
                    hoverinfo="text",
                    marker_color="#E1000F",
                    marker_symbol=marker_symbol,
                    marker_size=marker_size,
                    line_dash=marker_line_style,
                )
                mins_x.append(incoming_data_by_month["received_at"].min())
                maxs_y.append(incoming_data_by_month[variable_name].max())
                numbers_of_data_points.append(len(incoming_data_by_month))
                lines.append(incoming_line)

            if len(outgoing_data_by_month) > 0:
                outgoing_line = go.Scatter(
                    x=outgoing_data_by_month["sent_at"],
                    y=outgoing_data_by_month[variable_name],
                    name=outgoing_line_name,
                    mode="lines+markers",
                    hovertext=[
                        outgoing_hover_text.format(index.strftime("%B %y").capitalize(), format_number_str(e))
                        for index, e in outgoing_data_by_month.iter_rows()
                    ],
                    hoverinfo="text",
                    marker_color="#6A6AF4",
                    marker_symbol=marker_symbol,
                    marker_size=marker_size,
                    line_dash=marker_line_style,
                )
                mins_x.append(outgoing_data_by_month["sent_at"].min())
                maxs_y.append(outgoing_data_by_month[variable_name].max())
                numbers_of_data_points.append(len(outgoing_data_by_month))
                lines.append(outgoing_line)

        fig.add_traces(lines)

        dtick = "M2"
        if not numbers_of_data_points or max(numbers_of_data_points) < 3:
            dtick = "M1"

        tickangle = 0
        y_legend = -0.07
        if numbers_of_data_points and max(numbers_of_data_points) >= 15:
            tickangle = -90
            y_legend = -0.12

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={"orientation": "h", "y": y_legend, "x": 0},
            legend_font_size=11,
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        fig.update_xaxes(
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=min(mins_x) if mins_x else None,
            dtick=dtick,
            gridcolor="#ccc",
        )
        fig.update_yaxes(exponentformat="B", tickformat=".2s", gridcolor="#ccc", range=[0, max(maxs_y) * 1.2])

        self.figure = fig

    def build(self):
        self._preprocess_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class BsdTrackedAndRevisedProcessor:
    """Component with a Bar Figure of emitted, received and revised 'bordereaux'.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data: LazyFrame
        LazyFrame containing data for a given 'bordereau' type.
    data_date_interval: tuple
        Date interval to filter data.
    bs_revised_data: LazyFrame
        Optional LazyFrame containing list of revised 'bordereaux' for a given 'bordereau' type.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
        bs_revised_data: pl.LazyFrame | None = None,
    ) -> None:
        self.company_siret = company_siret
        self.bs_data = bs_data
        self.data_date_interval = data_date_interval
        self.bs_revised_data = bs_revised_data
        self.bs_emitted_by_month = None
        self.bs_received_by_month = None
        self.bs_revised_by_month = None

        self.figure = None

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it for plotting."""
        bs_data = self.bs_data

        bs_emitted = bs_data.filter(
            (pl.col("emitter_company_siret") == self.company_siret)
            & pl.col("sent_at").is_between(*self.data_date_interval)
        )

        bs_emitted_by_month = (
            bs_emitted.group_by(pl.col("sent_at").dt.truncate("1mo")).agg(pl.col("id").n_unique()).sort("sent_at")
        )

        bs_received = bs_data.filter(
            (pl.col("recipient_company_siret") == self.company_siret)
            & pl.col("received_at").is_between(*self.data_date_interval)
        )

        bs_received_by_month = (
            bs_received.group_by(pl.col("received_at").dt.truncate("1mo"))
            .agg(pl.col("id").n_unique())
            .sort("received_at")
        )

        self.bs_emitted_by_month = bs_emitted_by_month.collect()
        self.bs_received_by_month = bs_received_by_month.collect()

    def _preprocess_bs_revised_data(self) -> None:
        """Preprocess raw revised 'bordereaux' data to prepare it for plotting."""
        bs_revised_data = self.bs_revised_data

        if bs_revised_data is None:
            return

        bs_revised_data = bs_revised_data.filter(
            pl.col("bs_id").is_in(self.bs_data.select(pl.col("id")).collect()["id"].to_list())
            & pl.col("created_at").is_between(*self.data_date_interval)
        )
        bs_revised_by_month = (
            bs_revised_data.group_by(pl.col("created_at").dt.truncate("1mo"))
            .agg(pl.col("bs_id").n_unique())
            .sort("created_at")
        )

        self.bs_revised_by_month = bs_revised_by_month.collect()

    def _check_data_empty(self) -> bool:
        bs_emitted_by_month = self.bs_emitted_by_month
        bs_received_by_month = self.bs_received_by_month

        if len(bs_emitted_by_month) == len(bs_received_by_month) == 0:
            return True

        return False

    def _create_figure(self) -> None:
        bs_emitted_by_month = self.bs_emitted_by_month
        bs_received_by_month = self.bs_received_by_month
        bs_revised_by_month = self.bs_revised_by_month

        text_size = 12

        bs_emitted_bars = go.Bar(
            x=bs_emitted_by_month["sent_at"].to_list(),
            y=bs_emitted_by_month["id"].to_list(),
            name="Bordereaux émis",
            hovertext=[
                "{} - <b>{}</b> bordereau(x) émis".format(index.strftime("%B %y").capitalize(), e)
                for index, e in bs_emitted_by_month.iter_rows()
            ],
            hoverinfo="text",
            textfont_size=text_size,
            textposition="outside",
            constraintext="none",
            marker_color="#6A6AF4",
        )

        bs_received_bars = go.Bar(
            x=bs_received_by_month["received_at"].to_list(),
            y=bs_received_by_month["id"].to_list(),
            name="Bordereaux reçus",
            hovertext=[
                "{} - <b>{}</b> bordereau(x) reçus".format(index.strftime("%B %y").capitalize(), e)
                for index, e in bs_received_by_month.iter_rows()
            ],
            hoverinfo="text",
            textfont_size=text_size,
            textposition="outside",
            constraintext="none",
            marker_color="#E1000F",
        )

        if bs_emitted_by_month["sent_at"].min() is None:
            tick0_min = bs_received_by_month["received_at"].min()
        elif bs_received_by_month["received_at"].min() is None:
            tick0_min = bs_emitted_by_month["sent_at"].min()
        else:
            tick0_min = min(bs_received_by_month["received_at"].min(), bs_emitted_by_month["sent_at"].min())

        # Used to store the maximum value of each line
        # to be able to configure the height of the plotting area of the figure.
        max_y = max(bs_emitted_by_month["id"].max() or 0, bs_received_by_month["id"].max() or 0)

        fig = go.Figure([bs_emitted_bars, bs_received_bars])

        max_points = max(len(bs_emitted_by_month), len(bs_received_by_month))

        tickangle = 0
        y_legend = -0.07
        if max_points >= 15:
            tickangle = -90
            y_legend = -0.15

        if bs_revised_by_month is not None and len(bs_revised_by_month) > 0:
            fig.add_trace(
                go.Bar(
                    x=bs_revised_by_month["created_at"].to_list(),
                    y=bs_revised_by_month["bs_id"].to_list(),
                    name="Bordereaux corrigés",
                    hovertext=[
                        "{} - <b>{}</b> bordereau(x) révisés".format(index.strftime("%B %y").capitalize(), e)
                        for index, e in bs_revised_by_month.iter_rows()
                    ],
                    hoverinfo="text",
                    textfont_size=text_size,
                    textposition="outside",
                    constraintext="none",
                    marker_color="#B7A73F",
                )
            )
            tick0_min = min(tick0_min, bs_revised_by_month["created_at"].min())
            max_y = max(max_y, bs_revised_by_month["bs_id"].max())
            max_points = max(max_points, len(bs_revised_by_month))

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={
                "orientation": "h",
                "y": y_legend,
                "x": -0.1,
            },
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        ticklabelstep = 2
        if max_points <= 3:
            ticklabelstep = 1

        fig.update_xaxes(
            dtick=f"M{ticklabelstep}",
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=tick0_min,
            ticks="outside",
            gridcolor="#ccc",
        )

        # Range of the y axis is increased to increase the height of the plotting are of the figure
        fig.update_yaxes(range=[0, max_y * 1.1], gridcolor="#ccc")

        self.figure = fig

    def build(self):
        self._preprocess_bs_data()
        if self.bs_revised_data is not None:
            self._preprocess_bs_revised_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class WasteOriginProcessor:
    """Component with a bar figure representing the quantity of waste received by départements (only TOP 6).

    Parameters
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    departements_regions_df: LazyFrame
        Static data about regions and départements with their codes.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        departements_regions_df: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.bs_data_dfs = bs_data_dfs
        self.departements_regions_df = departements_regions_df
        self.data_date_interval = data_date_interval

        self.preprocessed_serie = None
        self.figure = None

    def _preprocess_data(self) -> None:
        if len(self.bs_data_dfs) == 0:
            return

        concat_df = pl.concat(
            [
                df.filter(pl.col("received_at").is_between(*self.data_date_interval))
                for df in self.bs_data_dfs.values()
            ],
            how="diagonal",
        )

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

        # We create the column `cp_formatted` that will hold the two first digit
        # (three in the case of DOM/TOM) of the postal code
        concat_df = concat_df.with_columns(
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
        if "quantity_refused" in concat_df.collect_schema().names():
            concat_df = concat_df.with_columns(
                (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                    "quantity_received"
                )
            )

        serie = (
            concat_df.filter(pl.col("recipient_company_siret") == self.company_siret)
            .group_by("cp_formatted")
            .agg(pl.col("quantity_received").sum())
            .filter(pl.col("quantity_received") > 0)
            .with_columns(pl.col("quantity_received").rank(descending=True).alias("rank"))
            .with_columns(
                pl.when(pl.col("rank") <= 5)
                .then("cp_formatted")
                .otherwise(pl.lit("Autres origines"))
                .alias("cp_formatted")  # Only TOP 5 'départements' are kept
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
            textfont_size=20,
            textposition="outside",
            width=[tup_e for e in values for tup_e in (0.7, 1)],
            hovertext=hovertexts,
            hoverinfo="text",
        )

        fig = go.Figure([bar_trace])
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False, type="category")
        fig.update_layout(
            margin={"t": 20, "b": 0, "l": 0, "r": 0},
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        self.figure = fig

    def build(self):
        self._preprocess_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class WasteOriginsMapProcessor:
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
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        departements_regions_df: pl.LazyFrame,
        regions_geodata: gpd.GeoDataFrame,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.bs_data_dfs = bs_data_dfs
        self.departements_regions_df = departements_regions_df
        self.regions_geodata = regions_geodata
        self.data_date_interval = data_date_interval

        self.preprocessed_df = None
        self.figure = None

    def _preprocess_data(self) -> None:
        if len(self.bs_data_dfs) == 0:
            return

        concat_df = pl.concat(
            [
                df.filter(pl.col("received_at").is_between(*self.data_date_interval))
                for df in self.bs_data_dfs.values()
            ],
            how="diagonal",
        )

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

        self._preprocess_data()

    def build(self):
        self._preprocess_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class ICPEDailyItemProcessor:
    """Component with a figure representing the quantity of waste processed by day for a particular ICPE "rubrique".


    Parameters:
    -----------
    icpe_item_daily_data: LazyFrame
        LazyFrame containing the waste processed data for a given ICPE "rubrique".
    """

    def __init__(
        self,
        icpe_item_daily_data: pl.LazyFrame,
    ) -> None:
        self.icpe_item_daily_data = icpe_item_daily_data

        self.preprocessed_df = None
        self.authorized_quantity = None
        self.mean_quantity = None

        self.figure = None

    def _preprocess_data(self) -> None:
        if self.icpe_item_daily_data is None:
            return

        df = self.icpe_item_daily_data.sort("day_of_processing")

        self.mean_quantity = df.select(pl.col("processed_quantity").mean()).collect().item()

        final_df = (
            df.group_by_dynamic(pl.col("day_of_processing"), every="1d")
            .agg(pl.col("processed_quantity").max().fill_null(0))
            .collect()
        )

        if len(final_df) > 0:
            self.preprocessed_df = final_df
            self.authorized_quantity = df.select(pl.col("authorized_quantity").max()).collect().item()

    def _check_data_empty(self) -> bool:
        if (self.preprocessed_df is None) or len(self.preprocessed_df) == 0:
            return True

        return False

    def _create_figure(self) -> None:
        df = self.preprocessed_df
        authorized_quantity = self.authorized_quantity
        trace = go.Scatter(
            x=df["day_of_processing"].to_list(),
            y=df["processed_quantity"].to_list(),
            hovertemplate="Le %{x|%d-%m-%Y} : <b>%{y:.2f}t</b> traitées<extra></extra>",
            line_width=1.5,
        )

        fig = go.Figure([trace])

        fig.update_layout(
            margin={"t": 40, "l": 35, "r": 70},
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
            title={
                "text": f"Quantité moyenne traitée par jour : <b>{format_number_str(self.mean_quantity, 2)}</b> t/j",
                "font_size": 14,
            },
        )

        max_y = df["processed_quantity"].max()
        if authorized_quantity is not None:
            fig.add_hline(
                y=authorized_quantity,
                line_dash="dot",
                line_color="red",
                line_width=3,
            )
            fig.add_annotation(
                xref="x domain",
                yref="y",
                x=1,
                y=authorized_quantity,
                text=f"Quantité maximale <br>autorisée :<b>{format_number_str(authorized_quantity, 2)}</b> t/jour",
                font_color="red",
                xanchor="left",
                showarrow=False,
                textangle=-90,
                font_size=13,
            )
            if authorized_quantity > max_y:
                max_y = authorized_quantity

        fig.update_yaxes(range=[0, max_y * 1.3], gridcolor="#ccc", title="Quantité traitée en tonnes")

        fig.update_xaxes(
            gridcolor="#ccc",
            zeroline=True,
            linewidth=1,
            linecolor="black",
            title="Date du traitement",
        )

        self.figure = fig

    def build(self):
        self._preprocess_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class ICPEAnnualItemProcessor:
    """
    Component with a figure representing the cummulative quantity of waste processed by day
    for a particular ICPE "rubrique".


    Parameters:
    -----------
    icpe_item_daily_data: LazyFrame
        LazyFrame containing the waste processed data for a given ICPE "rubrique".
    """

    def __init__(
        self,
        icpe_item_daily_data: pl.LazyFrame | None,
    ) -> None:
        self.icpe_item_daily_data = icpe_item_daily_data

        self.preprocessed_df = None
        self.authorized_quantity = None
        self.target_quantity = None

        self.figure = None

    def _preprocess_data(self) -> None:
        if self.icpe_item_daily_data is None:
            return

        df = self.icpe_item_daily_data.sort("day_of_processing")

        final_df = df.group_by_dynamic(pl.col("day_of_processing"), every="1d").agg(
            pl.col("processed_quantity").max().fill_null(0)
        )
        final_df = final_df.with_columns(
            pl.col("processed_quantity")
            .cum_sum()
            .over(partition_by=[pl.col("day_of_processing").dt.year()], order_by=pl.col("day_of_processing"))
            .alias("quantity_cumsum")
        ).collect()

        if len(final_df) > 0:
            self.preprocessed_df = final_df
            self.authorized_quantity = df.select(pl.col("authorized_quantity").max()).collect().item()
            self.target_quantity = df.select(pl.col("target_quantity").max()).collect().item()

    def _check_data_empty(self) -> bool:
        if (self.preprocessed_df is None) or len(self.preprocessed_df) == 0:
            return True

        if self.preprocessed_df["processed_quantity"].sum() == 0:
            return True

        return False

    def _create_figure(self) -> None:
        df = self.preprocessed_df
        authorized_quantity = self.authorized_quantity

        traces = []

        for year, temp_df in df.sort("day_of_processing").group_by(
            pl.col("day_of_processing").dt.year(), maintain_order=True
        ):
            trace = go.Scatter(
                x=temp_df["day_of_processing"].to_list(),
                y=temp_df["quantity_cumsum"].to_list(),
                hovertemplate="Le %{x|%d-%m-%Y} : <b>%{y:.2f}t</b> traitées au total sur l'année<extra></extra>",
                line_width=2,
            )

            traces.append(trace)

        fig = go.Figure(traces)

        for trace in traces[1:]:
            year = trace["x"][0].year
            x = min(trace["x"])
            fig.add_vline(
                line_dash="dot",
                line_color="black",
                line_width=2,
                x=x.timestamp() * 1000,
                # Due to this bug : https://github.com/plotly/plotly.py/issues/3065, we have to convert to epoch here
                annotation_text=f"{year}",
                annotation_position="top right",
            )

        fig.update_layout(
            margin={"t": 30, "l": 35, "r": 70},
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        max_y = df["quantity_cumsum"].max()
        if authorized_quantity is not None:
            fig.add_hline(
                y=authorized_quantity,
                line_dash="dot",
                line_color="red",
                line_width=3,
            )
            fig.add_annotation(
                xref="x domain",
                yref="y",
                x=1,
                y=authorized_quantity,
                text=f"Quantité maximale <br>autorisée : <b>{format_number_str(authorized_quantity, 2)}</b> t/an",
                font_color="red",
                xanchor="left",
                showarrow=False,
                textangle=-90,
                font_size=13,
            )

            target_quantity = self.target_quantity
            if target_quantity is not None:
                # Target for 2025
                fig.add_hline(
                    y=target_quantity,
                    line_dash="dot",
                    line_color="black",
                    line_width=2,
                )
                fig.add_annotation(
                    xref="x domain",
                    yref="y",
                    x=0.7,
                    y=target_quantity,
                    text=f"Seuil de TGAP majoré : <b>{format_number_str(target_quantity, 2)}</b> t/an",
                    font_color="black",
                    xanchor="left",
                    yanchor="bottom",
                    showarrow=False,
                    font_size=12,
                )

            if authorized_quantity > max_y:
                max_y = authorized_quantity

        fig.update_yaxes(
            range=[0, max_y * 1.3],
            gridcolor="#ccc",
            title="Quantité traitée en tonnes<br>(somme cumulée annuellement)",
        )

        fig.update_xaxes(
            range=[
                df["day_of_processing"].min(),
                df["day_of_processing"].max() + timedelta(days=7),
            ],
            gridcolor="#ccc",
            zeroline=True,
            linewidth=1,
            linecolor="black",
            title="Date du traitement",
        )

        self.figure = fig

    def build(self):
        self._preprocess_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class BsdaWorkerQuantityProcessor:
    """Component with a Line Figure of quantities linked to the worker company siret.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bsda_data_df: LazyFrame
        LazyFrame containing BSDA data.
    bsda_transporters_data_df : LazyFrame
        LazyFrames containing information about the transported BSDA waste.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        bsda_data_df: pl.LazyFrame,
        bsda_transporters_data_df: pl.LazyFrame | None,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.bsda_data = bsda_data_df
        self.bsda_transporters_data_df = bsda_transporters_data_df
        self.data_date_interval = data_date_interval

        self.quantities_signed_by_worker_by_month = None
        self.quantities_transported_by_month = None
        self.quantities_processed_by_month = None

        self.figure = None

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it for plotting."""
        bsda_data = self.bsda_data
        transport_df = self.bsda_transporters_data_df

        if (bsda_data is None) or (transport_df is None):
            return

        # Handling multimodal
        bsda_data = bsda_data.select(
            pl.selectors.exclude("sent_at")
        )  # To avoid column duplication with transport data

        bsda_data = bsda_data.join(
            transport_df.select(["bs_id", "sent_at", "transporter_company_siret"]),
            left_on="id",
            right_on="bs_id",
            how="left",
            validate="1:m",
        )

        bsda_data = bsda_data.group_by("id").agg(
            pl.col("worker_company_siret").max(),
            pl.col("quantity_received").max(),
            pl.col("waste_details_quantity").max(),
            pl.col("sent_at").min(),
            pl.col("processed_at").min(),
            pl.col("worker_work_signature_date").min(),
        )

        bsda_data = bsda_data.filter(pl.col("worker_company_siret") == self.company_siret)

        res = (
            bsda_data.filter(pl.col("worker_work_signature_date").is_between(*self.data_date_interval))
            .group_by(pl.col("worker_work_signature_date").dt.truncate("1mo").alias("date"))
            .agg(pl.col("waste_details_quantity").sum().alias("quantity_received"))
            .sort("date")
            .collect()
        )
        if len(res) > 0:
            self.quantities_signed_by_worker_by_month = res

        res = (
            bsda_data.filter(pl.col("sent_at").is_between(*self.data_date_interval))
            .group_by(pl.col("sent_at").dt.truncate("1mo").alias("date"))
            .agg(pl.col("quantity_received").sum())
            .sort("date")
            .collect()
        )
        if len(res) > 0:
            self.quantities_transported_by_month = res

        res = (
            bsda_data.filter(pl.col("processed_at").is_between(*self.data_date_interval))
            .group_by(pl.col("processed_at").dt.truncate("1mo").alias("date"))
            .agg(pl.col("quantity_received").sum())
            .sort("date")
            .collect()
        )
        if len(res) > 0:
            self.quantities_processed_by_month = res

    def _check_data_empty(self) -> bool:
        if all(
            (e is None) or (len(e) == 0)
            for e in [
                self.quantities_signed_by_worker_by_month,
                self.quantities_transported_by_month,
                self.quantities_processed_by_month,
            ]
        ):
            return True

        return False

    def _create_figure(self) -> None:
        lines = []

        configs = [
            {
                "data": self.quantities_signed_by_worker_by_month,
                "name": "Signé par l'entreprise de travaux",
                "hover_suffix": "tonnes (estimées)",
                "color": "#66673D",
            },
            {
                "data": self.quantities_transported_by_month,
                "name": "Enlevé par le transporteur",
                "hover_suffix": "tonnes enlevées",
                "color": "#E4794A",
            },
            {
                "data": self.quantities_processed_by_month,
                "name": "Traité",
                "hover_suffix": "tonnes traitées",
                "color": "#60E0EB",
            },
        ]

        tick0_min = None
        max_y = None
        max_points = 0
        for config in configs:
            data: pl.DataFrame | None = config["data"]
            hover_suffix = config["hover_suffix"]
            if data is not None and len(data) > 0:
                lines.append(
                    go.Scatter(
                        x=data["date"].to_list(),
                        y=data["quantity_received"].to_list(),
                        name=config["name"],
                        mode="lines+markers",
                        hovertext=[
                            f"{index.strftime('%B %y').capitalize()} - <b>{format_number_str(e, 2)}</b> {hover_suffix}"
                            for index, e in data.iter_rows()
                        ],
                        marker_color=config["color"],
                        line_color=config["color"],
                        hoverinfo="text",
                    )
                )
                min_ = data["date"].min()
                if (tick0_min is None) or (min_ < tick0_min):
                    tick0_min = min_

                max_ = data["quantity_received"].max()
                if (max_y is None) or (max_ < max_y):
                    max_y = max_

                if len(data) > max_points:
                    max_points = len(data)

        fig = go.Figure(lines)

        tickangle = 0
        y_legend = -0.07
        if max_points >= 15:
            tickangle = -90
            y_legend = -0.15

        dtick = "M2"
        if not max_points or max_points < 3:
            dtick = "M1"

        tickangle = 0
        y_legend = -0.07
        if max_points and max_points >= 15:
            tickangle = -90
            y_legend = -0.12

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={"orientation": "h", "y": y_legend, "x": 0},
            legend_font_size=11,
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        fig.update_xaxes(
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=tick0_min,
            dtick=dtick,
            gridcolor="#ccc",
        )
        fig.update_yaxes(exponentformat="B", tickformat=".2s", gridcolor="#ccc")

        self.figure = fig

    def build(self) -> str:
        self._preprocess_bs_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class TransporterBordereauxGraphProcessor:
    """Component with a Bar Figure showing monthly number of bordereaux as transporter company.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    transporters_data_df: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau transported data.
        Correspond to the new way of managing transporters in Trackdéchets.
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        transporters_data_df: Dict[str, pl.LazyFrame],  # Handling new multi-modal Trackdéchets feature
        bs_data_dfs: Dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.transporters_data_df = transporters_data_df
        self.bs_data_dfs = bs_data_dfs
        self.data_date_interval = data_date_interval

        self.transported_bordereaux_stats = {
            BSDD: None,
            BSDD_NON_DANGEROUS: None,
            BSDA: None,
            BSFF: None,
            BSDASRI: None,
            BSVHU: None,
        }

        self.figure = None

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it for plotting."""
        transporter_data_dfs = self.transporters_data_df
        bs_data_dfs = self.bs_data_dfs

        for bs_type, df in chain(transporter_data_dfs.items(), bs_data_dfs.items()):
            df = df.filter(
                pl.col("sent_at").is_between(*self.data_date_interval)
                & (pl.col("transporter_company_siret") == self.company_siret)
            )

            id_col = "bs_id" if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDA, BSFF] else "id"
            df_by_month = (
                df.group_by(pl.col("sent_at").dt.truncate("1mo"))
                .agg(pl.col(id_col).n_unique().alias("bs_count"))
                .collect()
            )
            if len(df_by_month) > 0:
                self.transported_bordereaux_stats[bs_type] = df_by_month

    def _check_data_empty(self) -> bool:
        if all((e is None) or (len(e) == 0) for e in self.transported_bordereaux_stats.values()):
            return True

        return False

    def _create_figure(self) -> None:
        bars = []

        configs = [
            {
                "data": self.transported_bordereaux_stats[BSDD],
                "name": "BSDD",
                "hover_suffix": "BSDD transportés",
            },
            {
                "data": self.transported_bordereaux_stats[BSDD_NON_DANGEROUS],
                "name": "BSDD Non Dangereux",
                "hover_suffix": "BSDD Non Dangereux transportés",
            },
            {
                "data": self.transported_bordereaux_stats[BSDA],
                "name": "BSDA",
                "hover_suffix": "BSDA transportés",
            },
            {
                "data": self.transported_bordereaux_stats[BSFF],
                "name": "BSFF",
                "hover_suffix": "BSFF transportés",
            },
            {
                "data": self.transported_bordereaux_stats[BSDASRI],
                "name": "BSDASRI",
                "hover_suffix": "BSDASRI transportés",
            },
            {
                "data": self.transported_bordereaux_stats[BSVHU],
                "name": "BSVHU",
                "hover_suffix": "BSVHU transportés",
            },
        ]

        tick0_min = None
        max_y = None
        max_points = 0
        for config in configs:
            data = config["data"]
            hover_suffix = config["hover_suffix"]
            if data is not None and len(data) > 0:
                bars.append(
                    go.Bar(
                        x=data["sent_at"].to_list(),
                        y=data["bs_count"].to_list(),
                        text=data["bs_count"].to_list(),
                        texttemplate="%{text:.0s}",
                        textposition="auto",
                        name=config["name"],
                        hovertext=[
                            f"{index.strftime('%B %y').capitalize()} - <b>{format_number_str(e, 2)}</b> {hover_suffix}"
                            for index, e in data.iter_rows()
                        ],
                        hoverinfo="text",
                    )
                )
                min_ = data["sent_at"].min()
                if (tick0_min is None) or (min_ < tick0_min):
                    tick0_min = min_

                max_ = data["bs_count"].max()
                if (max_y is None) or (max_ < max_y):
                    max_y = max_

                if len(data) > max_points:
                    max_points = len(data)

        fig = go.Figure(bars)

        tickangle = 0
        y_legend = -0.07
        if max_points >= 15:
            tickangle = -90
            y_legend = -0.15

        dtick = "M2"
        if not max_points or max_points < 3:
            dtick = "M1"

        tickangle = 0
        y_legend = -0.07
        if max_points and max_points >= 15:
            tickangle = -90
            y_legend = -0.12

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={"orientation": "h", "y": y_legend, "x": 0},
            legend_font_size=11,
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
            barmode="stack",
            margin_pad=5,
        )

        fig.update_xaxes(
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=tick0_min,
            dtick=dtick,
            gridcolor="#ccc",
        )
        fig.update_yaxes(exponentformat="B", tickformat=".2s", gridcolor="#ccc")

        self.figure = fig

    def build(self):
        self._preprocess_bs_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class TransportedQuantitiesGraphProcessor:
    """Component with a Line Figure showing monthly quantity fo waste transported company.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    transporters_data_df: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau transported data.
        Correspond to the new way of managing transporters in Trackdéchets.
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    data_date_interval: tuple
        Date interval to filter data.
    packagings_data_df : pl.LazyFrame | None
        Optional parameter that represents a LazyFrame containing data about BSFF packagings.
    """

    def __init__(
        self,
        company_siret: str,
        transporters_data_df: Dict[str, pl.LazyFrame],  # Handling new multi-modal Trackdéchets feature
        bs_data_dfs: Dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
        packagings_data_df: pl.LazyFrame | None = None,
    ) -> None:
        self.company_siret = company_siret
        self.transporters_data_df = transporters_data_df
        self.bs_data_dfs = bs_data_dfs
        self.data_date_interval = data_date_interval
        self.packagings_data_df = packagings_data_df

        self.transported_quantities_stats = {
            BSDD: None,
            BSDD_NON_DANGEROUS: None,
            BSDA: None,
            BSFF: None,
            BSDASRI: None,
            BSVHU: None,
        }

        self.figure = None

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it for plotting."""
        transporter_data_dfs = self.transporters_data_df
        bs_data_dfs = self.bs_data_dfs

        for bs_type, df in chain(transporter_data_dfs.items(), bs_data_dfs.items()):
            df = df.filter(
                pl.col("sent_at").is_between(*self.data_date_interval)
                & (pl.col("transporter_company_siret") == self.company_siret)
            )

            df_by_month = (
                df.group_by(pl.col("sent_at").dt.truncate("1mo")).agg(pl.col("quantity_received").sum()).collect()
            )
            if len(df_by_month) > 0:
                self.transported_quantities_stats[bs_type] = df_by_month

    def _check_data_empty(self) -> bool:
        if all((e is None) or (len(e) == 0) for e in self.transported_quantities_stats.values()):
            return True

        return False

    def _create_figure(self) -> None:
        bars = []

        configs = [
            {
                "data": self.transported_quantities_stats[BSDD],
                "name": "BSDD",
                "hover_text": "{} - <b>{}</b> tonnes de déchets dangereux transportés",
            },
            {
                "data": self.transported_quantities_stats[BSDD_NON_DANGEROUS],
                "name": "BSDD Non Dangereux",
                "hover_text": "{} - <b>{}</b> tonnes de déchets non dangereux transportés",
            },
            {
                "data": self.transported_quantities_stats[BSDA],
                "name": "BSDA",
                "hover_text": "{} - <b>{}</b> tonnes de déchets amiante transportés",
            },
            {
                "data": self.transported_quantities_stats[BSFF],
                "name": "BSFF",
                "hover_text": "{} - <b>{}</b> tonnes de déchets de fluides frigorigènes transportés",
            },
            {
                "data": self.transported_quantities_stats[BSDASRI],
                "name": "BSDASRI",
                "hover_text": "{} - <b>{}</b> tonnes de DASRI transportés",
            },
            {
                "data": self.transported_quantities_stats[BSVHU],
                "name": "BSVHU",
                "hover_text": "{} - <b>{}</b> tonnes de véhicules hors d'usage transportés",
            },
        ]

        tick0_min = None
        max_y = None
        max_points = 0
        for config in configs:
            data = config["data"]
            hover_text = config["hover_text"]
            if data is not None and len(data) > 0:
                bars.append(
                    go.Scatter(
                        x=data["sent_at"].to_list(),
                        y=data["quantity_received"].to_list(),
                        name=config["name"],
                        mode="lines+markers",
                        hovertext=[
                            hover_text.format(
                                index.strftime("%B %y").capitalize(),
                                format_number_str(e),
                            )
                            for index, e in data.iter_rows()
                        ],
                        hoverinfo="text",
                        stackgroup="one",
                    )
                )
                min_ = data["sent_at"].min()
                if (tick0_min is None) or (min_ < tick0_min):
                    tick0_min = min_

                max_ = data["quantity_received"].max()
                if (max_y is None) or (max_ < max_y):
                    max_y = max_

                if len(data) > max_points:
                    max_points = len(data)

        fig = go.Figure(bars)

        tickangle = 0
        y_legend = -0.07
        if max_points >= 15:
            tickangle = -90
            y_legend = -0.15

        dtick = "M2"
        if not max_points or max_points < 3:
            dtick = "M1"

        tickangle = 0
        y_legend = -0.07
        if max_points and max_points >= 15:
            tickangle = -90
            y_legend = -0.12

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={"orientation": "h", "y": y_legend, "x": 0},
            legend_font_size=11,
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
            margin_pad=5,
        )

        fig.update_xaxes(
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=tick0_min,
            dtick=dtick,
            gridcolor="#ccc",
        )
        fig.update_yaxes(exponentformat="B", tickformat=".2s", gridcolor="#ccc", ticksuffix="t")

        self.figure = fig

    def build(self):
        self._preprocess_bs_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class RegistryQuantitiesGraphProcessor:
    """Component with a Line Figure showing incoming and outgoing quantities of non dangerous waste.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    registry_incoming_data: LazyFrame
        LazyFrame containing data for incoming non dangerous waste (from registry).
    registry_outgoing_data: LazyFrame
        LazyFrame containing data for outgoing non dangerous waste (from registry).
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        registry_incoming_data: pl.LazyFrame | None,
        registry_outgoing_data: pl.LazyFrame | None,
        data_date_interval: tuple[datetime, datetime],
    ):
        self.company_siret = company_siret
        self.registry_incoming_data = registry_incoming_data
        self.registry_outgoing_data = registry_outgoing_data
        self.data_date_interval = data_date_interval

        self.incoming_weight_by_month_serie = None
        self.outgoing_weight_by_month_serie = None

        self.incoming_volume_by_month_serie = None
        self.outgoing_volume_by_month_serie = None

        self.figure = None

    def _preprocess_data(self) -> None:
        # We need to account for quantities in m³ and t
        for name, data, date_col in [
            ("incoming", self.registry_incoming_data, "reception_date"),
            ("outgoing", self.registry_outgoing_data, "dispatch_date"),
        ]:
            if data is not None:
                data = data.filter(
                    pl.col(date_col).is_between(*self.data_date_interval) & (pl.col("siret") == self.company_siret)
                )
                agg_series = []
                for colname in ("weight_value", "volume"):
                    agg_series.append(
                        data.group_by(pl.col(date_col).dt.truncate("1mo").alias("date"))
                        .agg(pl.col(colname).sum())
                        .sort("date")
                    )
                agg_series = pl.collect_all(agg_series)
                for serie, attr in zip(agg_series, ("{}_weight_by_month_serie", "{}_volume_by_month_serie")):
                    if len(serie) > 0:
                        setattr(self, attr.format(name), serie)

    def _check_data_empty(self) -> bool:
        series = [
            self.incoming_weight_by_month_serie,
            self.outgoing_weight_by_month_serie,
            self.incoming_volume_by_month_serie,
            self.outgoing_volume_by_month_serie,
        ]

        # If DataFrames are empty then output is empty
        if all((s is None) or (len(s) == 0) for s in series):
            return True

        return False

    def _create_figure(self) -> None:
        fig = go.Figure()

        lines = []  # Will store the lines graph objects

        # We store the minimum date of each series to be able to configure
        # the tick 0 of the figure
        mins_x = []

        # This is used to configure the dticks in case of low number of data points.
        numbers_of_data_points = []

        # We create two lines (for incoming and outgoing) for each quantity variable chosen
        for variable_name, incoming_data_by_month, outgoing_data_by_month in zip(
            ["weight_value", "volume"],
            [
                self.incoming_weight_by_month_serie,
                self.incoming_volume_by_month_serie,
            ],
            [self.outgoing_weight_by_month_serie, self.outgoing_volume_by_month_serie],
        ):
            incoming_line_name = "Quantité entrante (t)"
            incoming_hover_text = "{} - <b>{}</b> tonnes entrantes"
            outgoing_line_name = "Quantité sortante (t)"
            outgoing_hover_text = "{} - <b>{}</b> tonnes sortantes"
            marker_line_style = "solid"
            marker_symbol = "circle"
            marker_size = 6

            # To handle the case of volume
            if variable_name == "volume":
                incoming_line_name = "Volume entrant (m³)"
                incoming_hover_text = "{} - <b>{}</b> m³ entrants"
                outgoing_line_name = "Volume sortant (m³)"
                outgoing_hover_text = "{} - <b>{}</b> m³ sortants"
                marker_line_style = "dash"
                marker_symbol = "triangle-up"
                marker_size = 10

            if (incoming_data_by_month is not None) and len(incoming_data_by_month) > 0:
                incoming_line = go.Scatter(
                    x=incoming_data_by_month["date"].to_list(),
                    y=incoming_data_by_month[variable_name].to_list(),
                    name=incoming_line_name,
                    mode="lines+markers",
                    hovertext=[
                        incoming_hover_text.format(index.strftime("%B %y").capitalize(), format_number_str(e))
                        for index, e in incoming_data_by_month.select(
                            pl.col("date"), pl.col(variable_name)
                        ).iter_rows()
                    ],
                    hoverinfo="text",
                    marker_color="#E1000F",
                    marker_symbol=marker_symbol,
                    marker_size=marker_size,
                    line_dash=marker_line_style,
                )
                mins_x.append(incoming_data_by_month["date"].min())
                numbers_of_data_points.append(len(incoming_data_by_month))
                lines.append(incoming_line)

            if (outgoing_data_by_month is not None) and len(outgoing_data_by_month) > 0:
                outgoing_line = go.Scatter(
                    x=outgoing_data_by_month["date"].to_list(),
                    y=outgoing_data_by_month[variable_name].to_list(),
                    name=outgoing_line_name,
                    mode="lines+markers",
                    hovertext=[
                        outgoing_hover_text.format(index.strftime("%B %y").capitalize(), format_number_str(e))
                        for index, e in outgoing_data_by_month.select(
                            pl.col("date"), pl.col(variable_name)
                        ).iter_rows()
                    ],
                    hoverinfo="text",
                    marker_color="#6A6AF4",
                    marker_symbol=marker_symbol,
                    marker_size=marker_size,
                    line_dash=marker_line_style,
                )
                mins_x.append(outgoing_data_by_month["date"].min())
                numbers_of_data_points.append(len(outgoing_data_by_month))
                lines.append(outgoing_line)

        fig.add_traces(lines)

        dtick = "M2"
        if not numbers_of_data_points or max(numbers_of_data_points) < 3:
            dtick = "M1"

        tickangle = 0
        y_legend = -0.07
        if numbers_of_data_points and max(numbers_of_data_points) >= 15:
            tickangle = -90
            y_legend = -0.12

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={"orientation": "h", "y": y_legend, "x": 0},
            legend_font_size=11,
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        fig.update_xaxes(
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=min(mins_x) if mins_x else None,
            dtick=dtick,
            gridcolor="#ccc",
        )
        fig.update_yaxes(exponentformat="B", tickformat=".2s", gridcolor="#ccc")

        self.figure = fig

    def build(self):
        self._preprocess_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class RegistryStatementsGraphProcessor:
    """Component with a Bar Figure of incoming and outgoing registry statements.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    registry_incoming_data: LazyFrame
        LazyFrame containing data for incoming non dangerous waste (from registry).
    registry_outgoing_data: LazyFrame
        LazyFrame containing data for outgoing non dangerous waste (from registry).
    statement_type: str
        Type of statement used as input, either non dangerous waste statements, excavated lands statements or ssd.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        registry_incoming_data: pl.LazyFrame | None,
        registry_outgoing_data: pl.LazyFrame | None,
        statement_type: Literal["non_dangerous_waste"] | Literal["excavated_land"] | Literal["ssd"],
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.registry_incoming_data = registry_incoming_data
        self.registry_outgoing_data = registry_outgoing_data
        self.statement_type = statement_type
        self.data_date_interval = data_date_interval

        self.statements_emitted_by_month_serie = None
        self.statements_received_by_month_serie = None

        self.figure = None

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw registry data to prepare it for plotting."""

        for name, data, date_col in [
            ("received", self.registry_incoming_data, "reception_date"),
            ("emitted", self.registry_outgoing_data, "dispatch_date"),
        ]:
            if data is not None:
                data = data.filter(
                    pl.col(date_col).is_between(*self.data_date_interval) & (pl.col("siret") == self.company_siret)
                )
                agg_serie = (
                    data.group_by(pl.col(date_col).dt.truncate("1mo").alias("date"))
                    .agg(pl.col("id").count())
                    .sort("date")
                    .collect()
                )

                attr = f"statements_{name}_by_month_serie"
                if len(agg_serie) > 0:
                    setattr(self, attr, agg_serie)

    def _check_data_empty(self) -> bool:
        match [self.statements_emitted_by_month_serie, self.statements_received_by_month_serie]:
            case [None, None]:
                return True
            case [df, None] | [None, df]:
                if len(df) == 0:
                    return True
            case [df1, df2]:
                if len(df1) == len(df2) == 0:
                    return True

        return False

    def _create_figure(self) -> None:
        statements_emitted_by_month = self.statements_emitted_by_month_serie
        statements_received_by_month = self.statements_received_by_month_serie

        text_size = 12

        bars = []
        ticks0 = []
        nums_points = []
        # Used to store the maximum value of each line
        # to be able to configure the height of the plotting area of the figure.
        max_y = 0

        match self.statement_type:
            case "non_dangerous_waste":
                name = "DND"
                hover_suffix = "déchets non dangereux"
            case "excavated_land":
                name = "TEXS"
                hover_suffix = "TEXS"
            case "ssd":
                name = "SSD"
                hover_suffix = "sorties de statut de déchet"
            case _:
                hover_suffix = ""

        if (statements_emitted_by_month is not None) and (len(statements_emitted_by_month) > 0):
            statements_emitted_bars = go.Bar(
                x=statements_emitted_by_month["date"],
                y=statements_emitted_by_month["id"],
                name=f"{name} - sortant",
                hovertext=[
                    "{} - <b>{}</b> déclaration(s) sortante(s) de {}".format(
                        index.strftime("%B %y").capitalize(), e, hover_suffix
                    )
                    for index, e in statements_emitted_by_month.iter_rows()
                ],
                hoverinfo="text",
                textfont_size=text_size,
                textposition="outside",
                constraintext="none",
                marker_color="#6A6AF4",
            )
            ticks0.append(statements_emitted_by_month["date"].min())
            max_y = max(max_y, statements_emitted_by_month["id"].max())
            nums_points.append(len(statements_emitted_by_month))
            bars.append(statements_emitted_bars)

        if (statements_received_by_month is not None) and (len(statements_received_by_month) > 0):
            statements_received_bars = go.Bar(
                x=statements_received_by_month["date"],
                y=statements_received_by_month["id"],
                name=f"{name} - entrant",
                hovertext=[
                    "{} - <b>{}</b> déclaration(s) de {}".format(index.strftime("%B %y").capitalize(), e, hover_suffix)
                    for index, e in statements_received_by_month.iter_rows()
                ],
                hoverinfo="text",
                textfont_size=text_size,
                textposition="outside",
                constraintext="none",
                marker_color="#E1000F",
            )
            ticks0.append(statements_received_by_month["date"].min())
            max_y = max(max_y, statements_received_by_month["id"].max())
            nums_points.append(len(statements_received_by_month))
            bars.append(statements_received_bars)

        tick0_min = min(ticks0)

        fig = go.Figure(bars)

        max_points = max(nums_points)

        tickangle = 0
        y_legend = -0.07
        if max_points >= 15:
            tickangle = -90
            y_legend = -0.15

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={
                "orientation": "h",
                "y": y_legend,
                "x": -0.1,
            },
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        ticklabelstep = 2
        if max_points <= 3:
            ticklabelstep = 1

        fig.update_xaxes(
            dtick=f"M{ticklabelstep}",
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=tick0_min,
            ticks="outside",
            gridcolor="#ccc",
        )

        # Range of the y axis is increased to increase the height of the plotting are of the figure
        fig.update_yaxes(range=[0, max_y * 1.1], gridcolor="#ccc")

        self.figure = fig

    def build(self):
        self._preprocess_bs_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class IntermediaryBordereauxCountsGraphProcessor:
    """Component with a Bar Figure showing monthly number of bordereaux sent
    as "eco-organisme" or other type of intermediary.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    transporters_data_df: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau transported data.
        Correspond to the new way of managing transporters in Trackdéchets.
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        transporters_data_df: Dict[str, pl.LazyFrame],  # Handling new multi-modal Trackdéchets feature
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.bs_data_dfs = bs_data_dfs
        self.transporters_data_df = transporters_data_df
        self.data_date_interval = data_date_interval

        self.bordereaux_stats = {
            BSDD: None,
            BSDD_NON_DANGEROUS: None,
            BSDA: None,
            BSDASRI: None,
        }

        self.figure = None

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it for plotting."""
        bs_data_dfs = self.bs_data_dfs

        for bs_type, df in bs_data_dfs.items():
            df = df
            if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDA]:
                transport_df = self.transporters_data_df.get(bs_type)

                if transport_df is None:
                    continue

                df = df.select(pl.selectors.exclude("sent_at"))  # To avoid column duplication with transport data

                df = df.join(
                    transport_df.select(["bs_id", "sent_at"]),
                    left_on="id",
                    right_on="bs_id",
                    how="left",
                    validate="1:m",
                )

            df = df.filter(
                pl.col("sent_at").is_between(*self.data_date_interval)
                & (pl.col("eco_organisme_siret") == self.company_siret)
            )

            df_by_month = df.group_by(pl.col("sent_at").dt.truncate("1mo")).agg(pl.col("id").n_unique()).collect()
            if len(df_by_month) > 0:
                self.bordereaux_stats[bs_type] = df_by_month

    def _check_data_empty(self) -> bool:
        if all((e is None) or (len(e) == 0) for e in self.bordereaux_stats.values()):
            return True

        return False

    def _create_figure(self) -> None:
        bars = []

        configs = [
            {
                "data": self.bordereaux_stats[BSDD],
                "name": "BSDD",
                "hover_suffix": "BSDD traités",
            },
            {
                "data": self.bordereaux_stats[BSDD_NON_DANGEROUS],
                "name": "BSDD Non Dangereux",
                "hover_suffix": "BSDD Non Dangereux traités",
            },
            {
                "data": self.bordereaux_stats[BSDA],
                "name": "BSDA",
                "hover_suffix": "BSDA traités",
            },
            {
                "data": self.bordereaux_stats[BSDASRI],
                "name": "BSDASRI",
                "hover_suffix": "BSDASRI traités",
            },
        ]

        tick0_min = None
        max_y = None
        max_points = 0
        for config in configs:
            data = config["data"]
            hover_suffix = config["hover_suffix"]
            if data is not None and len(data) > 0:
                bars.append(
                    go.Bar(
                        x=data["sent_at"],
                        y=data["id"],
                        text=data,
                        texttemplate="%{text:.0s}",
                        textposition="auto",
                        name=config["name"],
                        hovertext=[
                            f"{index.strftime('%B %y').capitalize()} - <b>{format_number_str(e, 2)}</b> {hover_suffix}"
                            for index, e in data.iter_rows()
                        ],
                        hoverinfo="text",
                    )
                )
                min_ = data["sent_at"].min()
                if (tick0_min is None) or (min_ < tick0_min):
                    tick0_min = min_

                max_ = data["id"].max()
                if (max_y is None) or (max_ < max_y):
                    max_y = max_

                if len(data) > max_points:
                    max_points = len(data)

        fig = go.Figure(bars)

        tickangle = 0
        y_legend = -0.07
        if max_points >= 15:
            tickangle = -90
            y_legend = -0.15

        dtick = "M2"
        if not max_points or max_points < 3:
            dtick = "M1"

        tickangle = 0
        y_legend = -0.07
        if max_points and max_points >= 15:
            tickangle = -90
            y_legend = -0.12

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={"orientation": "h", "y": y_legend, "x": 0},
            legend_font_size=11,
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
            barmode="stack",
            margin_pad=5,
        )

        fig.update_xaxes(
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=tick0_min,
            dtick=dtick,
            gridcolor="#ccc",
        )
        fig.update_yaxes(exponentformat="B", tickformat=".2s", gridcolor="#ccc")

        self.figure = fig

    def build(self):
        self._preprocess_bs_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class IntermediaryBordereauxQuantitiesGraphProcessor:
    """Component with a Bar Figure showing monthly number of bordereaux sent
    as "eco-organisme" or other type of intermediary.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    transporters_data_df: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau transported data.
        Correspond to the new way of managing transporters in Trackdéchets.
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        transporters_data_df: Dict[str, pl.LazyFrame],  # Handling new multi-modal Trackdéchets feature
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.bs_data_dfs = bs_data_dfs
        self.transporters_data_df = transporters_data_df
        self.data_date_interval = data_date_interval

        self.bordereaux_stats = {
            BSDD: None,
            BSDD_NON_DANGEROUS: None,
            BSDA: None,
            BSDASRI: None,
        }

        self.figure = None

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it for plotting."""
        bs_data_dfs = self.bs_data_dfs

        for bs_type, df in bs_data_dfs.items():
            if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDA]:
                transport_df = self.transporters_data_df.get(bs_type)

                if transport_df is None:
                    continue

                df = df.select(pl.selectors.exclude("sent_at"))  # To avoid column duplication with transport data

                df = df.join(
                    transport_df.select(["bs_id", "sent_at"]),
                    left_on="id",
                    right_on="bs_id",
                    how="left",
                    validate="1:m",
                )

            df = df.filter(
                pl.col("sent_at").is_between(*self.data_date_interval)
                & (pl.col("eco_organisme_siret") == self.company_siret)
            ).unique(subset=["id"])

            if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDASRI]:
                df = df.with_columns(
                    (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                        "quantity_received"
                    )
                )

            df_by_month = (
                df.group_by(pl.col("sent_at").dt.truncate("1mo")).agg(pl.col("quantity_received").sum()).collect()
            )

            if len(df_by_month) > 0:
                self.bordereaux_stats[bs_type] = df_by_month

    def _check_data_empty(self) -> bool:
        if all((e is None) or (len(e) == 0) for e in self.bordereaux_stats.values()):
            return True

        return False

    def _create_figure(self) -> None:
        bars = []

        configs = [
            {
                "data": self.bordereaux_stats[BSDD],
                "name": "BSDD",
                "hover_text": "{} - <b>{}</b> tonnes de déchets dangereux",
            },
            {
                "data": self.bordereaux_stats[BSDD_NON_DANGEROUS],
                "name": "BSDD Non Dangereux",
                "hover_text": "{} - <b>{}</b> tonnes de déchets non dangereux",
            },
            {
                "data": self.bordereaux_stats[BSDA],
                "name": "BSDA",
                "hover_text": "{} - <b>{}</b> tonnes de déchets amiante",
            },
            {
                "data": self.bordereaux_stats[BSDASRI],
                "name": "BSDASRI",
                "hover_text": "{} - <b>{}</b> tonnes de DASRI",
            },
        ]

        tick0_min = None
        max_y = None
        max_points = 0
        for config in configs:
            data = config["data"]
            hover_text = config["hover_text"]
            if data is not None and len(data) > 0:
                bars.append(
                    go.Scatter(
                        x=data["sent_at"],
                        y=data["quantity_received"],
                        name=config["name"],
                        mode="lines+markers",
                        hovertext=[
                            hover_text.format(
                                index.strftime("%B %y").capitalize(),
                                format_number_str(e),
                            )
                            for index, e in data.iter_rows()
                        ],
                        hoverinfo="text",
                        stackgroup="one",
                    )
                )
                min_ = data["sent_at"].min()
                if (tick0_min is None) or (min_ < tick0_min):
                    tick0_min = min_

                max_ = data["quantity_received"].max()
                if (max_y is None) or (max_ < max_y):
                    max_y = max_

                if len(data) > max_points:
                    max_points = len(data)

        fig = go.Figure(bars)

        tickangle = 0
        y_legend = -0.07
        if max_points >= 15:
            tickangle = -90
            y_legend = -0.15

        dtick = "M2"
        if not max_points or max_points < 3:
            dtick = "M1"

        tickangle = 0
        y_legend = -0.07
        if max_points and max_points >= 15:
            tickangle = -90
            y_legend = -0.12

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={"orientation": "h", "y": y_legend, "x": 0},
            legend_font_size=11,
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
            margin_pad=5,
        )

        fig.update_xaxes(
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=tick0_min,
            dtick=dtick,
            gridcolor="#ccc",
        )
        fig.update_yaxes(exponentformat="B", tickformat=".2s", gridcolor="#ccc", ticksuffix="t")

        self.figure = fig

    def build(self):
        self._preprocess_bs_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class RegistryTransporterStatementsStatsGraphProcessor:
    """Component with a Bar Figure showing monthly number of registry statements as transporter company.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    registry_data: dict
        Dict with key being the registry data type and values the LazyFrame containing the statements data.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        registry_data: Dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.registry_data = registry_data
        self.data_date_interval = data_date_interval

        self.transported_statements_stats = {
            "ndw_incoming": None,
            "ndw_outgoing": None,
            "excavated_land_incoming": None,
            "excavated_land_outgoing": None,
        }

        self.figure = None

    def _preprocess_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it for plotting."""
        registry_data = self.registry_data

        for key, date_col in [
            ("ndw_incoming", "reception_date"),
            ("ndw_outgoing", "dispatch_date"),
            ("excavated_land_incoming", "reception_date"),
            ("excavated_land_outgoing", "dispatch_date"),
        ]:
            df = registry_data[key]

            if df is None:
                continue

            df = df.filter(
                pl.col(date_col).is_between(*self.data_date_interval)
                & (pl.col("transporters_org_ids").list.contains(pl.lit(self.company_siret)))
            )

            df_by_month = (
                df.group_by(pl.col(date_col).dt.truncate("1mo").alias("date"))
                .agg(pl.col("id").n_unique().alias("number_statements"))
                .collect()
            )
            if len(df_by_month) > 0:
                self.transported_statements_stats[key] = df_by_month

    def _check_data_empty(self) -> bool:
        if all((e is None) or (len(e) == 0) for e in self.transported_statements_stats.values()):
            return True

        return False

    def _create_figure(self) -> None:
        bars = []

        configs = [
            {
                "data": self.transported_statements_stats["ndw_incoming"],
                "name": "DND transportés (entrant)",
                "hover_suffix": "déclaration(s) de DND transportés (registre entrant)",
            },
            {
                "data": self.transported_statements_stats["ndw_outgoing"],
                "name": "DND transportés (sortant)",
                "hover_suffix": "déclaration(s) de DND transportés (registre sortant)",
            },
            {
                "data": self.transported_statements_stats["excavated_land_incoming"],
                "name": "TEXS transportés (entrant)",
                "hover_suffix": "déclaration(s) de TEXS transportés (registre entrant)",
            },
            {
                "data": self.transported_statements_stats["excavated_land_outgoing"],
                "name": "TEXS transportés (sortant)",
                "hover_suffix": "déclaration(s) de TEXS transportés (registre sortant)",
            },
        ]

        tick0_min = None
        max_y = None
        max_points = 0
        for config in configs:
            data = config["data"]
            hover_suffix = config["hover_suffix"]
            if data is not None and len(data) > 0:
                bars.append(
                    go.Bar(
                        x=data["date"],
                        y=data["number_statements"],
                        text=data["number_statements"],
                        texttemplate="%{text:.0s}",
                        textposition="auto",
                        name=config["name"],
                        hovertext=[
                            f"{index.strftime('%B %y').capitalize()} - <b>{format_number_str(e, 2)}</b> {hover_suffix}"
                            for index, e in data.iter_rows()
                        ],
                        hoverinfo="text",
                    )
                )
                min_ = data["date"].min()
                if (tick0_min is None) or (min_ < tick0_min):
                    tick0_min = min_

                max_ = data["number_statements"].max()
                if (max_y is None) or (max_ < max_y):
                    max_y = max_

                if len(data) > max_points:
                    max_points = len(data)

        fig = go.Figure(bars)

        tickangle = 0
        y_legend = -0.07
        if max_points >= 15:
            tickangle = -90
            y_legend = -0.15

        dtick = "M2"
        if not max_points or max_points < 3:
            dtick = "M1"

        tickangle = 0
        y_legend = -0.07
        if max_points and max_points >= 15:
            tickangle = -90
            y_legend = -0.12

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={"orientation": "h", "y": y_legend, "x": 0},
            legend_font_size=11,
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
            barmode="stack",
            margin_pad=5,
        )

        fig.update_xaxes(
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=tick0_min,
            dtick=dtick,
            gridcolor="#ccc",
        )
        fig.update_yaxes(exponentformat="B", tickformat=".2s", gridcolor="#ccc")

        self.figure = fig

    def build(self):
        self._preprocess_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure


class RegistryTransporterQuantitiesGraphProcessor:
    """Component with a Bar Figure showing monthly number of waste quantity transported from registry data.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    registry_data: dict
        Dict with key being the registry data type and values the LazyFrame containing the statements data.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        registry_data: Dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.registry_data = registry_data
        self.data_date_interval = data_date_interval

        self.transported_quantities_stats = {
            "ndw_incoming": {"T": None, "M3": None},
            "ndw_outgoing": {"T": None, "M3": None},
            "excavated_land_incoming": {"T": None, "M3": None},
            "excavated_land_outgoing": {"T": None, "M3": None},
        }

        self.figure = None

    def _preprocess_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it for plotting."""
        registry_data = self.registry_data

        for key, date_col in [
            ("ndw_incoming", "reception_date"),
            ("ndw_outgoing", "dispatch_date"),
            ("excavated_land_incoming", "reception_date"),
            ("excavated_land_outgoing", "dispatch_date"),
        ]:
            df = registry_data[key]

            if df is None:
                continue

            for quantity_col in ["weight_value", "volume"]:  # Handle multiple units
                df = df.filter(
                    pl.col(date_col).is_between(*self.data_date_interval)
                    & pl.col("transporters_org_ids").list.contains(pl.lit(self.company_siret))
                ).filter(pl.col(quantity_col) > 0)

                df_by_month = (
                    df.group_by(pl.col(date_col).dt.truncate("1mo").alias("date"))
                    .agg(pl.col(quantity_col).sum())
                    .collect()
                )
                if len(df_by_month) > 0:
                    self.transported_quantities_stats[key][quantity_col] = df_by_month

    def _check_data_empty(self) -> bool:
        if all(
            (ee is None) or (len(ee) == 0) for e in self.transported_quantities_stats.values() for ee in e.values()
        ):
            return True

        return False

    def _create_figure(self) -> None:
        bars = []

        configs = [
            {
                "data": self.transported_quantities_stats["ndw_incoming"],
                "name": "DND transportés (entrant)",
                "hover_suffix": "de DND transportés (registre entrant)",
            },
            {
                "data": self.transported_quantities_stats["ndw_outgoing"],
                "name": "DND transportés (sortant)",
                "hover_suffix": "de DND transportés (registre sortant)",
            },
            {
                "data": self.transported_quantities_stats["excavated_land_incoming"],
                "name": "TEXS transportés (entrant)",
                "hover_suffix": "de TEXS transportés (registre entrant)",
            },
            {
                "data": self.transported_quantities_stats["excavated_land_outgoing"],
                "name": "TEXS transportés (sortant)",
                "hover_suffix": "de TEXS transportés (registre sortant)",
            },
        ]

        tick0_min = None
        max_y = None
        max_points = 0
        for config in configs:
            data = config["data"]
            hover_suffix = config["hover_suffix"]
            if data != {}:
                for quantity_col, data_df in data.items():
                    if (data_df is None) or len(data_df) == 0:
                        continue

                    data_temp = data_df.select(["date", quantity_col])

                    unit_str = "t"
                    unit_name_str = "masse"
                    marker_line_style = "solid"
                    marker_symbol = "circle"
                    marker_size = 6
                    if quantity_col == "volume":
                        unit_str = "m³"
                        unit_name_str = "volume"
                        marker_line_style = "dash"
                        marker_symbol = "triangle-up"
                        marker_size = 10

                    bars.append(
                        go.Scatter(
                            x=data_temp["date"],
                            y=data_temp[quantity_col],
                            name=f"{unit_name_str.capitalize()} de {config['name']}",
                            mode="lines+markers",
                            hovertext=[
                                f"{index.strftime('%B %y').capitalize()} - <b>{format_number_str(e, 2)}<b>{unit_str} {hover_suffix}"
                                for index, e in data_temp.iter_rows()
                            ],
                            hoverinfo="text",
                            stackgroup="one",
                            line_dash=marker_line_style,
                            marker_symbol=marker_symbol,
                            marker_size=marker_size,
                        )
                    )
                    min_ = data_df["date"].min()
                    if (tick0_min is None) or (min_ < tick0_min):
                        tick0_min = min_

                    max_ = data_df[quantity_col].max()
                    if (max_y is None) or (max_ < max_y):
                        max_y = max_

                    if len(data_df) > max_points:
                        max_points = len(data_df)

        fig = go.Figure(bars)

        tickangle = 0
        y_legend = -0.07
        if max_points >= 15:
            tickangle = -90
            y_legend = -0.15

        dtick = "M2"
        if not max_points or max_points < 3:
            dtick = "M1"

        tickangle = 0
        y_legend = -0.07
        if max_points and max_points >= 15:
            tickangle = -90
            y_legend = -0.12

        fig.update_layout(
            margin={"t": 20, "l": 35, "r": 5},
            legend={"orientation": "h", "y": y_legend, "x": 0},
            legend_font_size=11,
            legend_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            paper_bgcolor="#fff",
            plot_bgcolor="rgba(0,0,0,0)",
            margin_pad=5,
        )

        fig.update_xaxes(
            tickangle=tickangle,
            tickformat="%b %y",
            tick0=tick0_min,
            dtick=dtick,
            gridcolor="#ccc",
        )
        fig.update_yaxes(exponentformat="B", tickformat=".2s", gridcolor="#ccc", ticksuffix="t")

        self.figure = fig

    def build(self):
        self._preprocess_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure
