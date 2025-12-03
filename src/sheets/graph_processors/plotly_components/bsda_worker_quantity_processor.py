from datetime import datetime

import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str


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
