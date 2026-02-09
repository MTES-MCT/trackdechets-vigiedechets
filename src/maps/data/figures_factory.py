"""This modules contains all the functions to create the Plotly figure needed for the ICPE maps."""

from datetime import datetime, timedelta

import plotly.graph_objects as go
import polars as pl

from ..constants import ANNUAL_ICPE_RUBRIQUES, DAILY_ICPE_RUBRIQUES, MIN_TGAP_INFO_YEAR

gridcolor = "#ccc"


def create_icpe_graph(df: pl.DataFrame, key_column: str | None, rubrique: str) -> str:
    authorized_quantity = df.select(pl.col("quantite_autorisee").max()).item()

    target_quantity = None
    if "quantite_objectif" in df.columns:
        target_quantity = df.select(pl.col("quantite_objectif").max()).item()

    df_waste = df.filter(pl.col("day_of_processing").is_not_null())
    if len(df_waste) == 0:
        return None

    if rubrique in ANNUAL_ICPE_RUBRIQUES:
        group_by_expr = pl.col("day_of_processing").dt.truncate("1mo")
        df_waste = df_waste.group_by(group_by_expr).agg(pl.col("quantite_traitee").sum())
        df_waste = df_waste.sort(pl.col("day_of_processing")).with_columns(
            pl.col("quantite_traitee").cum_sum().alias("quantite_traitee_cumulee")
        )

        trace_hover_template = "En %{x|%B} : <b>%{y:.2f}t</b> traitées<extra></extra>"
        trace_name = "Quantité mensuelle traitée"
        trace_x_axis_margin = 30
        trace_xaxis_tickformat = "%b %y"
        trace_dtick = "M1"
        gaph_class = go.Bar
        authorized_quantity_unit = "t/an"
    
    elif rubrique in DAILY_ICPE_RUBRIQUES:
        group_by_expr = pl.col("day_of_processing").dt.truncate("1d")
        df_waste = df_waste.group_by(group_by_expr).agg(pl.col("quantite_traitee").sum())
        df_waste = df_waste.sort(pl.col("day_of_processing")).with_columns(
            pl.col("quantite_traitee").cum_sum().alias("quantite_traitee_cumulee")
        )

        trace_hover_template = "Le %{x|%d-%m-%Y} : <b>%{y:.2f}t</b> traitées<extra></extra>"
        trace_name = "Quantité journalière traitée"
        trace_x_axis_margin = 7
        trace_xaxis_tickformat = None
        trace_dtick = None
        gaph_class = go.Scatter
        authorized_quantity_unit = "t/j"

    data = df_waste.to_dict(as_series=False)

    traces = []
    traces.append(
        gaph_class(
            x=data["day_of_processing"],
            y=data["quantite_traitee"],
            hovertemplate=trace_hover_template,
            name=trace_name,
            marker_color="#8D533E",
        )
    )
    
    traces.append(
        go.Scatter(
            x=data["day_of_processing"],
            y=data["quantite_traitee_cumulee"],
            texttemplate="%{y:.2s}t",
            textposition="top center",
            hovertemplate="En %{x|%B} : <b>%{y:.2f}t</b> traitées en cummulé sur l'année<extra></extra>",
            line_width=2,
            name="Quantité traitée cummulée",
            line_color="#272747",
            mode="lines+text+markers",
        )
    )

    max_y = max(e for e in data["quantite_traitee"] if e is not None)
    max_y = max(e for e in data["quantite_traitee_cumulee"] if e is not None)

    fig = go.Figure(traces)

    fig.update_layout(
        margin={"t": 30, "l": 35, "r": 80},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            bgcolor="rgba(0,0,0,0)",
            x=1,
        ),
        paper_bgcolor="#fff",
        plot_bgcolor="rgba(0,0,0,0)",
        autosize=True,
        height=400,
    )

    if authorized_quantity:
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
            text=f"Quantité maximale <br>autorisée : <b>{authorized_quantity:.0f}</b> {authorized_quantity_unit}",
            font_color="red",
            xanchor="left",
            showarrow=False,
            textangle=-90,
            font_size=13,
        )
        max_y = max(max_y, authorized_quantity)
        current_year = min(data["day_of_processing"]).year
        if target_quantity is not None and current_year >= MIN_TGAP_INFO_YEAR:
            fig.add_hline(
                y=target_quantity,
                line_dash="dot",
                line_color="black",
                line_width=2,
            )
            fig.add_annotation(
                xref="x domain",
                yref="y",
                x=0,
                y=target_quantity,
                text=f"Seuil de TGAP majoré :{target_quantity:.0f} {authorized_quantity_unit}",
                font_color="black",
                xanchor="left",
                yanchor="bottom",
                showarrow=False,
                font_size=13,
            )
            max_y = max(max_y, target_quantity)

    fig.update_yaxes(gridcolor="#ccc", title="tonnes", tick0=0, range=[0, max_y * 1.3])

    fig.update_xaxes(
        range=[
            datetime(year=min(data["day_of_processing"]).year, month=1, day=1) - timedelta(days=trace_x_axis_margin),
            datetime(year=min(data["day_of_processing"]).year, month=12, day=31) + timedelta(days=trace_x_axis_margin),
        ],
        tickformat=trace_xaxis_tickformat,
        tick0=min(data["day_of_processing"]),
        dtick=trace_dtick,
        gridcolor="#ccc",
        zeroline=True,
        linewidth=1,
        linecolor="black",
    )

    res = fig.to_json()
    if key_column is not None:
        pivot_value = df.select(pl.col(key_column).max()).item()
        res = pl.DataFrame([[pivot_value], [fig.to_json()]], [key_column, "graph"])
    return res
