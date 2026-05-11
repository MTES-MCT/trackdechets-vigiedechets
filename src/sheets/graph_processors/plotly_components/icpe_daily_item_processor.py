from datetime import datetime

import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str


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
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.icpe_item_daily_data = icpe_item_daily_data
        self.data_date_interval = data_date_interval
        self.preprocessed_df = None
        self.authorized_quantity = None
        self.mean_quantity = None

        self.figure = None

    def _preprocess_data(self) -> None:
        if self.icpe_item_daily_data is None:
            return

        df = self.icpe_item_daily_data.filter(
            pl.col("day_of_processing").is_between(*self.data_date_interval, closed="both")
        ).sort("day_of_processing")

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
