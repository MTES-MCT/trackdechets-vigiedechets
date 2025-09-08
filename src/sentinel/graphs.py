import plotly.graph_objects as go
import polars as pl

from registry.constants import RegistryV2WasteCode
from sentinel.colors import GRAPH_COLORS
from sentinel.data_extraction import (
    get_dept_waste_quantity_total,
    get_national_waste_quantity_total,
    get_top_five_waste_code_by_naf,
)
from sentinel.queries import STATS_BY_NAF_AND_DEPARTMENT_QUERY
from sheets.data_extraction import build_query


def truncate_with_ellipsis(str, length):
    if len(str) <= length:
        return str
    return f"{str[length]}…"


def format_nb_spaces(number: int):
    return f"{number:_}".replace("_", " ")


def build_bar_graph(values, short_labels, labels, waste_quantity_total):
    traces = []
    for i, (value, short_label, label, color) in enumerate(zip(values, short_labels, labels, GRAPH_COLORS)):
        round_percentage = round(value, 1)
        traces.append(
            go.Bar(
                x=[value],
                y=[short_label],
                orientation="h",
                marker=dict(color=color, line=dict(color="#fff", width=1)),
                text=[f"{round_percentage} % "],
                texttemplate="%{text}",
                textposition="inside",
                textfont=dict(color="white", size=12),
                name=label,
                showlegend=True,
            )
        )
    fig = go.Figure(data=traces)
    fig.update_layout(
        template="plotly_white",
        autosize=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
        ),
        margin={"l": 0, "t": 30, "b": 0, "r": 0, "pad": 0},
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor="lightgray",
        ),
        yaxis=dict(title="", showgrid=False, categoryorder="total descending"),
        font=dict(family="Marianne, arial, sans-serif", color="#333333"),
        height=500,  # Adjust height as needed
    )
    fig.add_annotation(
        text=f'<span style="color: #000000; font-weight:bold">Total: {waste_quantity_total} t</span>',
        x=0.5,
        y=1.1,
        xref="paper",
        yref="paper",
        font_size=16,
        xanchor="center",
        showarrow=False,
        font=dict(color="#333333", family="Marianne, arial, sans-serif"),
    )

    res = fig.to_json()

    return res


def build_national_graph(naf_code):
    waste_quantity_total = get_national_waste_quantity_total(naf_code)

    stats_dicts = get_top_five_waste_code_by_naf(naf_code)
    if not stats_dicts:  # for testing
        return {}
    stats_df = pl.from_dicts(stats_dicts)

    stats_df = stats_df.with_columns(waste_quantity_share_percent=(pl.col("waste_quantity_share") * 100).round(2))

    values = stats_df["waste_quantity_share_percent"]

    waste_quantity_share_percent_sum = stats_df["waste_quantity_share_percent"].sum()
    waste_quantity_share_percent_remaining = 100 - waste_quantity_share_percent_sum
    remaining = pl.Series([waste_quantity_share_percent_remaining], dtype=pl.Float64)

    values.extend(remaining)

    short_labels = list(stats_df["waste_code"]) + ["Autres"]
    labels = [RegistryV2WasteCode(waste_code).label for waste_code in stats_df["waste_code"]]

    other = pl.Series(["Autres"])
    labels.extend(other)

    return build_bar_graph(values, short_labels, labels, waste_quantity_total)


def build_department_graph(naf_code, department):
    national_stats_dicts = get_top_five_waste_code_by_naf(naf_code)
    waste_codes = [row["waste_code"] for row in national_stats_dicts]

    waste_quantity_total = get_dept_waste_quantity_total(naf_code, department)
    stats_df = build_query(
        STATS_BY_NAF_AND_DEPARTMENT_QUERY,
        query_params={"naf_code": naf_code, "department": department, "waste_codes": waste_codes},
    )

    stats_df = stats_df.with_columns(waste_quantity_share_percent=(pl.col("waste_quantity_share") * 100).round(2))

    values = stats_df["waste_quantity_share_percent"]

    waste_quantity_share_percent_sum = stats_df["waste_quantity_share_percent"].sum()

    waste_quantity_share_percent_remaining = 100 - waste_quantity_share_percent_sum
    remaining = pl.Series([waste_quantity_share_percent_remaining], dtype=pl.Float64)

    values.extend(remaining)

    short_labels = list(stats_df["waste_code"]) + ["Autres"]
    labels = [RegistryV2WasteCode(waste_code).label for waste_code in stats_df["waste_code"]]
    other = pl.Series(["Autres"])
    labels.extend(other)

    return build_bar_graph(values, short_labels, labels, waste_quantity_total)
