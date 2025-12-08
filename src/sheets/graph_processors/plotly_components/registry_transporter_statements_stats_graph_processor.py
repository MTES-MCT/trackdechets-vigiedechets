from datetime import datetime
from typing import Dict

import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str


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
