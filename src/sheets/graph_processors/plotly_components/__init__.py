"""Plotly components processors module.

This module contains processors that generate serialized (JSON) plotly visualizations
to be consumed by plotly scripts. Each processor is in its own file for better maintainability.
"""

import locale

# Set up French locale for date formatting
# classes returning a serialized (json) plotly visualization to be consumed by a plotly script
try:
    locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
except locale.Error:
    # Fallback for systems where French locale isn't available
    try:
        locale.setlocale(locale.LC_ALL, "fr_FR")
    except locale.Error:
        print("Warning: French locale not available, using default")
        locale.setlocale(locale.LC_ALL, "")

from .bsd_quantities_graph import BsdQuantitiesGraph
from .bsd_tracked_and_revised_processor import BsdTrackedAndRevisedProcessor
from .bsda_worker_quantity_processor import BsdaWorkerQuantityProcessor
from .icpe_annual_item_processor import ICPEAnnualItemProcessor
from .icpe_daily_item_processor import ICPEDailyItemProcessor
from .intermediary_bordereaux_counts_graph_processor import IntermediaryBordereauxCountsGraphProcessor
from .intermediary_bordereaux_quantities_graph_processor import IntermediaryBordereauxQuantitiesGraphProcessor
from .registry_quantities_graph_processor import RegistryQuantitiesGraphProcessor
from .registry_statements_graph_processor import RegistryStatementsGraphProcessor
from .registry_transporter_quantities_graph_processor import RegistryTransporterQuantitiesGraphProcessor
from .registry_transporter_statements_stats_graph_processor import RegistryTransporterStatementsStatsGraphProcessor
from .transported_quantities_graph_processor import TransportedQuantitiesGraphProcessor
from .transporter_bordereaux_graph_processor import TransporterBordereauxGraphProcessor
from .waste_origin_processor import WasteOriginProcessor
from .waste_origins_map_processor import WasteOriginsMapProcessor

__all__ = [
    "BsdaWorkerQuantityProcessor",
    "BsdQuantitiesGraph",
    "BsdTrackedAndRevisedProcessor",
    "ICPEAnnualItemProcessor",
    "ICPEDailyItemProcessor",
    "IntermediaryBordereauxCountsGraphProcessor",
    "IntermediaryBordereauxQuantitiesGraphProcessor",
    "RegistryQuantitiesGraphProcessor",
    "RegistryStatementsGraphProcessor",
    "RegistryTransporterQuantitiesGraphProcessor",
    "RegistryTransporterStatementsStatsGraphProcessor",
    "TransportedQuantitiesGraphProcessor",
    "TransporterBordereauxGraphProcessor",
    "WasteOriginProcessor",
    "WasteOriginsMapProcessor",
]
