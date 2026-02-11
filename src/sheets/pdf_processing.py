from sheets.data_processing import bsds_config
from sheets.models import ComputedInspectionData
from sheets.plotly_utils import data_to_bs64_plot


def render_pdf_fn(computed_pk):
    computed = ComputedInspectionData.objects.get(pk=computed_pk)

    for config in bsds_config:
        bsd_type = config["bsd_type"]
        created_rectified_data = getattr(computed, f"{bsd_type}_created_rectified_data")
        setattr(
            computed,
            f"{bsd_type}_created_rectified_graph",
            data_to_bs64_plot(created_rectified_data),
        )
        stock_data = getattr(computed, f"{bsd_type}_stock_data")
        setattr(computed, f"{bsd_type}_stock_graph", data_to_bs64_plot(stock_data))

    for icpe_graph in ["icpe_2770", "icpe_2790", "icpe_2760_1", "icpe_2771", "icpe_2791", "icpe_2760_2"]:
        icpe_graph_data = getattr(computed, f"{icpe_graph}_data")
        if icpe_graph_data:
            setattr(
                computed,
                f"{icpe_graph}_graph",
                data_to_bs64_plot(icpe_graph_data),
            )

    computed.save()
