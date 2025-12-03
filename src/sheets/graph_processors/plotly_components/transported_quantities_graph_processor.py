from datetime import datetime
from itertools import chain
from typing import Dict

import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str

from ...constants import BSDA, BSDASRI, BSDD, BSDD_NON_DANGEROUS, BSFF, BSVHU


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
