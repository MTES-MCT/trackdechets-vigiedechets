from datetime import datetime
from typing import Dict

import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str


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
            "ndw_incoming": {"weight_value": None, "volume": None},
            "ndw_outgoing": {"weight_value": None, "volume": None},
            "excavated_land_incoming": {"weight_value": None, "volume": None},
            "excavated_land_outgoing": {"weight_value": None, "volume": None},
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
                filtered_df = df.filter(
                    pl.col(date_col).is_between(*self.data_date_interval)
                    & pl.col("transporters_org_ids").list.contains(pl.lit(self.company_siret))
                ).filter(pl.col(quantity_col) > 0)

                df_by_month = (
                    filtered_df.group_by(pl.col(date_col).dt.truncate("1mo").alias("date"))
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
