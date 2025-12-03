from datetime import datetime

import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str


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
