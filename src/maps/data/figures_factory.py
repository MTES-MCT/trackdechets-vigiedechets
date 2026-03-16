"""This modules contains all the functions to create the Plotly figure needed for the ICPE maps."""

from datetime import datetime, timedelta

import plotly.graph_objects as go
import polars as pl

from ..constants import ANNUAL_ICPE_RUBRIQUES, DAILY_ICPE_RUBRIQUES, MIN_TGAP_INFO_YEAR

gridcolor = "#ccc"


def _xaxis_range(data: dict, margin_days: int) -> list:
    year = min(data["day_of_processing"]).year
    return [
        datetime(year=year, month=1, day=1) - timedelta(days=margin_days),
        datetime(year=year, month=12, day=31) + timedelta(days=margin_days),
    ]


def _base_layout(**extra) -> dict:
    return dict(
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
        **extra,
    )


def _add_thresholds(
    fig: go.Figure,
    authorized_quantity: float,
    unit: str,
    annotation_x: float,
    annotation_xanchor: str,
    target_quantity: float | None,
    current_year: int,
    max_y: float,
) -> float:
    fig.add_hline(y=authorized_quantity, line_dash="dot", line_color="red", line_width=3)
    fig.add_annotation(
        xref="x domain",
        yref="y",
        x=annotation_x,
        y=authorized_quantity,
        text=f"Quantité maximale <br>autorisée : <b>{authorized_quantity:.0f}</b> {unit}",
        font_color="red",
        xanchor=annotation_xanchor,
        textangle=90,
        showarrow=False,
        font_size=13,
    )
    max_y = max(max_y, authorized_quantity)

    if target_quantity is not None and current_year >= MIN_TGAP_INFO_YEAR:
        fig.add_hline(y=target_quantity, line_dash="dot", line_color="black", line_width=2)
        fig.add_annotation(
            xref="x domain",
            yref="y",
            x=0,
            y=target_quantity,
            text=f"Seuil de TGAP majoré :{target_quantity:.0f} {unit}",
            font_color="black",
            xanchor="left",
            yanchor="bottom",
            showarrow=False,
            font_size=13,
        )
        max_y = max(max_y, target_quantity)

    return max_y


def _shared_xaxis_kwargs(
    data: dict, margin_days: int, tickformat: str | None = None, dtick: str | None = None
) -> dict:
    return dict(
        range=_xaxis_range(data, margin_days),
        tick0=min(data["day_of_processing"]),
        tickformat=tickformat,
        dtick=dtick,
        gridcolor=gridcolor,
        zeroline=True,
        linewidth=1,
        linecolor="black",
    )


def create_icpe_graph(df: pl.DataFrame, key_column: str | None, rubrique: str):
    authorized_quantity = df.select(pl.col("quantite_autorisee").max()).item()

    target_quantity = None
    if "quantite_objectif" in df.columns:
        target_quantity = df.select(pl.col("quantite_objectif").max()).item()

    df_waste = df.filter(pl.col("day_of_processing").is_not_null())
    if len(df_waste) == 0:
        if key_column is not None:
            pivot_value = df.select(pl.col(key_column).max()).item()
            return pl.DataFrame(
                {key_column: [pivot_value], "graph": [None], "graph_cumul": [None]},
                schema={key_column: pl.Utf8, "graph": pl.Utf8, "graph_cumul": pl.Utf8},
            )
        return (None, None)

    if rubrique in ANNUAL_ICPE_RUBRIQUES:
        df_waste = (
            df_waste.group_by(pl.col("day_of_processing").dt.truncate("1mo"))
            .agg(pl.col("quantite_traitee").sum())
            .sort("day_of_processing")
            .with_columns(pl.col("quantite_traitee").cum_sum().alias("quantite_traitee_cumulee"))
        )
        data = df_waste.to_dict(as_series=False)

        max_y = max(
            max(e for e in data["quantite_traitee"] if e is not None),
            max(e for e in data["quantite_traitee_cumulee"] if e is not None),
        )

        fig = go.Figure(
            [
                go.Bar(
                    x=data["day_of_processing"],
                    y=data["quantite_traitee"],
                    hovertemplate="En %{x|%B} : <b>%{y:.2f}t</b> traitées<extra></extra>",
                    name="Quantité mensuelle traitée",
                    marker_color="#0c4201",
                ),
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
                ),
            ]
        )
        fig.update_layout(
            **_base_layout(margin={"t": 50, "l": 35, "r": 80}), title="Quantité mensuelle traitée et cumulée"
        )

        if authorized_quantity:
            current_year = min(data["day_of_processing"]).year
            max_y = _add_thresholds(fig, authorized_quantity, "t/an", 1, "right", target_quantity, current_year, max_y)

        fig.update_yaxes(gridcolor=gridcolor, title="tonnes", tick0=0, range=[0, max_y * 1.3])
        fig.update_xaxes(**_shared_xaxis_kwargs(data, margin_days=30, tickformat="%b %y", dtick="M1"))

        main_json = fig.to_json()
        cumul_json = None

    elif rubrique in DAILY_ICPE_RUBRIQUES:
        df_waste = (
            df_waste.group_by(pl.col("day_of_processing").dt.truncate("1d"))
            .agg(pl.col("quantite_traitee").sum())
            .sort("day_of_processing")
            .with_columns(pl.col("quantite_traitee").cum_sum().alias("quantite_traitee_cumulee"))
        )
        data = df_waste.to_dict(as_series=False)

        max_daily = max(e for e in data["quantite_traitee"] if e is not None)
        max_cumul = max(e for e in data["quantite_traitee_cumulee"] if e is not None)
        current_year = min(data["day_of_processing"]).year
        xaxis_kwargs = _shared_xaxis_kwargs(data, margin_days=7)

        # --- Figure 1: daily quantities ---
        fig_main = go.Figure(
            [
                go.Scatter(
                    x=data["day_of_processing"],
                    y=data["quantite_traitee"],
                    hovertemplate="Le %{x|%d-%m-%Y} : <b>%{y:.2f}t</b> traitées<extra></extra>",
                    name="Quantité journalière traitée",
                    line_color="#8D533E",
                )
            ]
        )
        fig_main.update_layout(
            **_base_layout(margin={"t": 50, "l": 35, "r": 80}), title="Quantité journalière traitée"
        )

        max_y_main = max_daily
        if authorized_quantity:
            max_y_main = _add_thresholds(
                fig_main, authorized_quantity, "t/j", 1, "right", target_quantity, current_year, max_y_main
            )

        fig_main.update_yaxes(gridcolor=gridcolor, title="t/j", tick0=0, range=[0, max_y_main * 1.3])
        fig_main.update_xaxes(**xaxis_kwargs)

        # --- Figure 2: cumulative quantities ---
        fig_cumul = go.Figure(
            [
                go.Scatter(
                    x=data["day_of_processing"],
                    y=data["quantite_traitee_cumulee"],
                    hovertemplate="Le %{x|%d-%m-%Y} : <b>%{y:.2f}t</b> cumulées<extra></extra>",
                    name="Quantité traitée cumulée",
                    line_color="#272747",
                    mode="lines",
                )
            ]
        )
        fig_cumul.update_layout(**_base_layout(margin={"t": 50, "l": 35, "r": 80}), title="Quantité traitée cumulée")
        fig_cumul.update_yaxes(gridcolor=gridcolor, title="tonnes (cumulé)", tick0=0, range=[0, max_cumul * 1.3])
        fig_cumul.update_xaxes(**xaxis_kwargs)

        main_json = fig_main.to_json()
        cumul_json = fig_cumul.to_json()

    if key_column is not None:
        pivot_value = df.select(pl.col(key_column).max()).item()
        return pl.DataFrame(
            {key_column: [pivot_value], "graph": [main_json], "graph_cumul": [cumul_json]},
            schema={key_column: pl.Utf8, "graph": pl.Utf8, "graph_cumul": pl.Utf8},
        )
    return (main_json, cumul_json)
