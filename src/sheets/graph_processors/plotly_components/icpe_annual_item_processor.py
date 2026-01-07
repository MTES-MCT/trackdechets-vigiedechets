from datetime import timedelta, datetime

import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str


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
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.icpe_item_daily_data = icpe_item_daily_data
        self.data_date_interval = data_date_interval
        self.preprocessed_df = None
        self.authorized_quantity = None
        self.target_quantity = None

        self.figure = None

    def _preprocess_data(self) -> None:
        if self.icpe_item_daily_data is None:
            return

        df = self.icpe_item_daily_data.filter(
            pl.col("day_of_processing").is_between(*self.data_date_interval, closed="both")
        ).sort("day_of_processing")

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
