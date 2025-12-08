from datetime import datetime
from typing import Literal

import plotly.graph_objects as go
import polars as pl


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
