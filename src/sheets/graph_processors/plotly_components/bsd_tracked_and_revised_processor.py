from datetime import datetime

import plotly.graph_objects as go
import polars as pl


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
