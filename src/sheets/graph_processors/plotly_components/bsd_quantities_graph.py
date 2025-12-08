from datetime import datetime

import plotly.graph_objects as go
import polars as pl

from sheets.utils import format_number_str

from ...constants import BSDASRI, BSDD, BSDD_NON_DANGEROUS, BSFF


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
