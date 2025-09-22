import json

from sheets.plotly_utils import data_to_bs64_plot

data = {
    "data": [
        {
            "constraintext": "none",
            "hoverinfo": "text",
            "hovertext": [
                "Janvier 24 - <b>34</b> bordereau(x) émis",
                "Février 24 - <b>28</b> bordereau(x) émis",
                "Mars 24 - <b>34</b> bordereau(x) émis",
                "Avril 24 - <b>29</b> bordereau(x) émis",
                "Mai 24 - <b>25</b> bordereau(x) émis",
                "Juin 24 - <b>16</b> bordereau(x) émis",
                "Juillet 24 - <b>18</b> bordereau(x) émis",
                "Août 24 - <b>19</b> bordereau(x) émis",
                "Septembre 24 - <b>16</b> bordereau(x) émis",
                "Octobre 24 - <b>16</b> bordereau(x) émis",
                "Novembre 24 - <b>21</b> bordereau(x) émis",
                "Décembre 24 - <b>23</b> bordereau(x) émis",
            ],
            "marker": {"color": "#6A6AF4"},
            "name": "Bordereaux émis",
            "textfont": {"size": 12},
            "textposition": "outside",
            "x": [
                "2024-01-31T00:00:00",
                "2024-02-29T00:00:00",
                "2024-03-31T00:00:00",
                "2024-04-30T00:00:00",
                "2024-05-31T00:00:00",
                "2024-06-30T00:00:00",
                "2024-07-31T00:00:00",
                "2024-08-31T00:00:00",
                "2024-09-30T00:00:00",
                "2024-10-31T00:00:00",
                "2024-11-30T00:00:00",
                "2024-12-31T00:00:00",
            ],
            "y": [34, 28, 34, 29, 25, 16, 18, 19, 16, 16, 21, 23],
            "type": "bar",
        },
        {
            "constraintext": "none",
            "hoverinfo": "text",
            "hovertext": [],
            "marker": {"color": "#E1000F"},
            "name": "Bordereaux reçus",
            "textfont": {"size": 12},
            "textposition": "outside",
            "x": [],
            "y": [],
            "type": "bar",
        },
    ],
    "layout": {
        "template": {
            "data": {
                "histogram2dcontour": [
                    {
                        "type": "histogram2dcontour",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0.0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1.0, "#f0f921"],
                        ],
                    }
                ],
                "choropleth": [{"type": "choropleth", "colorbar": {"outlinewidth": 0, "ticks": ""}}],
                "histogram2d": [
                    {
                        "type": "histogram2d",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0.0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1.0, "#f0f921"],
                        ],
                    }
                ],
                "heatmap": [
                    {
                        "type": "heatmap",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0.0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1.0, "#f0f921"],
                        ],
                    }
                ],
                "heatmapgl": [
                    {
                        "type": "heatmapgl",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0.0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1.0, "#f0f921"],
                        ],
                    }
                ],
                "contourcarpet": [{"type": "contourcarpet", "colorbar": {"outlinewidth": 0, "ticks": ""}}],
                "contour": [
                    {
                        "type": "contour",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0.0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1.0, "#f0f921"],
                        ],
                    }
                ],
                "surface": [
                    {
                        "type": "surface",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0.0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1.0, "#f0f921"],
                        ],
                    }
                ],
                "mesh3d": [{"type": "mesh3d", "colorbar": {"outlinewidth": 0, "ticks": ""}}],
                "scatter": [{"fillpattern": {"fillmode": "overlay", "size": 10, "solidity": 0.2}, "type": "scatter"}],
                "parcoords": [{"type": "parcoords", "line": {"colorbar": {"outlinewidth": 0, "ticks": ""}}}],
                "scatterpolargl": [
                    {"type": "scatterpolargl", "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}}}
                ],
                "bar": [
                    {
                        "error_x": {"color": "#2a3f5f"},
                        "error_y": {"color": "#2a3f5f"},
                        "marker": {
                            "line": {"color": "#E5ECF6", "width": 0.5},
                            "pattern": {"fillmode": "overlay", "size": 10, "solidity": 0.2},
                        },
                        "type": "bar",
                    }
                ],
                "scattergeo": [{"type": "scattergeo", "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}}}],
                "scatterpolar": [{"type": "scatterpolar", "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}}}],
                "histogram": [
                    {"marker": {"pattern": {"fillmode": "overlay", "size": 10, "solidity": 0.2}}, "type": "histogram"}
                ],
                "scattergl": [{"type": "scattergl", "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}}}],
                "scatter3d": [
                    {
                        "type": "scatter3d",
                        "line": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                        "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                    }
                ],
                "scattermapbox": [{"type": "scattermapbox", "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}}}],
                "scatterternary": [
                    {"type": "scatterternary", "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}}}
                ],
                "scattercarpet": [{"type": "scattercarpet", "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}}}],
                "carpet": [
                    {
                        "aaxis": {
                            "endlinecolor": "#2a3f5f",
                            "gridcolor": "white",
                            "linecolor": "white",
                            "minorgridcolor": "white",
                            "startlinecolor": "#2a3f5f",
                        },
                        "baxis": {
                            "endlinecolor": "#2a3f5f",
                            "gridcolor": "white",
                            "linecolor": "white",
                            "minorgridcolor": "white",
                            "startlinecolor": "#2a3f5f",
                        },
                        "type": "carpet",
                    }
                ],
                "table": [
                    {
                        "cells": {"fill": {"color": "#EBF0F8"}, "line": {"color": "white"}},
                        "header": {"fill": {"color": "#C8D4E3"}, "line": {"color": "white"}},
                        "type": "table",
                    }
                ],
                "barpolar": [
                    {
                        "marker": {
                            "line": {"color": "#E5ECF6", "width": 0.5},
                            "pattern": {"fillmode": "overlay", "size": 10, "solidity": 0.2},
                        },
                        "type": "barpolar",
                    }
                ],
                "pie": [{"automargin": True, "type": "pie"}],
            },
            "layout": {
                "autotypenumbers": "strict",
                "colorway": [
                    "#636efa",
                    "#EF553B",
                    "#00cc96",
                    "#ab63fa",
                    "#FFA15A",
                    "#19d3f3",
                    "#FF6692",
                    "#B6E880",
                    "#FF97FF",
                    "#FECB52",
                ],
                "font": {"color": "#2a3f5f"},
                "hovermode": "closest",
                "hoverlabel": {"align": "left"},
                "paper_bgcolor": "white",
                "plot_bgcolor": "#E5ECF6",
                "polar": {
                    "bgcolor": "#E5ECF6",
                    "angularaxis": {"gridcolor": "white", "linecolor": "white", "ticks": ""},
                    "radialaxis": {"gridcolor": "white", "linecolor": "white", "ticks": ""},
                },
                "ternary": {
                    "bgcolor": "#E5ECF6",
                    "aaxis": {"gridcolor": "white", "linecolor": "white", "ticks": ""},
                    "baxis": {"gridcolor": "white", "linecolor": "white", "ticks": ""},
                    "caxis": {"gridcolor": "white", "linecolor": "white", "ticks": ""},
                },
                "coloraxis": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                "colorscale": {
                    "sequential": [
                        [0.0, "#0d0887"],
                        [0.1111111111111111, "#46039f"],
                        [0.2222222222222222, "#7201a8"],
                        [0.3333333333333333, "#9c179e"],
                        [0.4444444444444444, "#bd3786"],
                        [0.5555555555555556, "#d8576b"],
                        [0.6666666666666666, "#ed7953"],
                        [0.7777777777777778, "#fb9f3a"],
                        [0.8888888888888888, "#fdca26"],
                        [1.0, "#f0f921"],
                    ],
                    "sequentialminus": [
                        [0.0, "#0d0887"],
                        [0.1111111111111111, "#46039f"],
                        [0.2222222222222222, "#7201a8"],
                        [0.3333333333333333, "#9c179e"],
                        [0.4444444444444444, "#bd3786"],
                        [0.5555555555555556, "#d8576b"],
                        [0.6666666666666666, "#ed7953"],
                        [0.7777777777777778, "#fb9f3a"],
                        [0.8888888888888888, "#fdca26"],
                        [1.0, "#f0f921"],
                    ],
                    "diverging": [
                        [0, "#8e0152"],
                        [0.1, "#c51b7d"],
                        [0.2, "#de77ae"],
                        [0.3, "#f1b6da"],
                        [0.4, "#fde0ef"],
                        [0.5, "#f7f7f7"],
                        [0.6, "#e6f5d0"],
                        [0.7, "#b8e186"],
                        [0.8, "#7fbc41"],
                        [0.9, "#4d9221"],
                        [1, "#276419"],
                    ],
                },
                "xaxis": {
                    "gridcolor": "white",
                    "linecolor": "white",
                    "ticks": "",
                    "title": {"standoff": 15},
                    "zerolinecolor": "white",
                    "automargin": True,
                    "zerolinewidth": 2,
                },
                "yaxis": {
                    "gridcolor": "white",
                    "linecolor": "white",
                    "ticks": "",
                    "title": {"standoff": 15},
                    "zerolinecolor": "white",
                    "automargin": True,
                    "zerolinewidth": 2,
                },
                "scene": {
                    "xaxis": {
                        "backgroundcolor": "#E5ECF6",
                        "gridcolor": "white",
                        "linecolor": "white",
                        "showbackground": True,
                        "ticks": "",
                        "zerolinecolor": "white",
                        "gridwidth": 2,
                    },
                    "yaxis": {
                        "backgroundcolor": "#E5ECF6",
                        "gridcolor": "white",
                        "linecolor": "white",
                        "showbackground": True,
                        "ticks": "",
                        "zerolinecolor": "white",
                        "gridwidth": 2,
                    },
                    "zaxis": {
                        "backgroundcolor": "#E5ECF6",
                        "gridcolor": "white",
                        "linecolor": "white",
                        "showbackground": True,
                        "ticks": "",
                        "zerolinecolor": "white",
                        "gridwidth": 2,
                    },
                },
                "shapedefaults": {"line": {"color": "#2a3f5f"}},
                "annotationdefaults": {"arrowcolor": "#2a3f5f", "arrowhead": 0, "arrowwidth": 1},
                "geo": {
                    "bgcolor": "white",
                    "landcolor": "#E5ECF6",
                    "subunitcolor": "white",
                    "showland": True,
                    "showlakes": True,
                    "lakecolor": "white",
                },
                "title": {"x": 0.05},
                "mapbox": {"style": "light"},
            },
        },
        "margin": {"t": 20, "l": 35, "r": 5},
        "legend": {"orientation": "h", "y": -0.07, "x": -0.1, "bgcolor": "rgba(0,0,0,0)"},
        "showlegend": True,
        "paper_bgcolor": "#fff",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "xaxis": {
            "dtick": "M2",
            "tickangle": 0,
            "tickformat": "%b %y",
            "tick0": "2024-01-31T00:00:00",
            "ticks": "outside",
            "gridcolor": "#ccc",
        },
        "yaxis": {"range": [0, 37.400000000000006], "gridcolor": "#ccc"},
    },
}


def test_data_to_bs64_plot():
    """
    Test plotly graph to png conversion through kaleido.
    It prevents pdf rendering fails due to plotly/kaleido breaking changes.
    """
    data_to_bs64_plot(json.dumps(data))
