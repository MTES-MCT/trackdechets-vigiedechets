"""HTML components processors module.

This module contains processors that generate data structures for HTML templates.
Each processor is in its own file for better maintainability.
"""

from .bsd_canceled_table_processor import BsdCanceledTableProcessor
from .bsd_refused_table_processor import BsdRefusedTableProcessor
from .bsd_stats_processor import BsdStatsProcessor
from .bsda_worker_stats_processor import BsdaWorkerStatsProcessor
from .followed_with_pnttd_table_processor import FollowedWithPNTTDTableProcessor
from .gistrid_stats_processor import GistridStatsProcessor
from .icpe_items_processor import ICPEItemsProcessor
from .incinerator_outgoing_waste_processor import IncineratorOutgoingWasteProcessor
from .intermediary_bordereaux_stats_processor import IntermediaryBordereauxStatsProcessor
from .linked_companies_processor import LinkedCompaniesProcessor
from .private_individuals_collections_table_processor import PrivateIndividualsCollectionsTableProcessor
from .quantity_outliers_table_processor import QuantityOutliersTableProcessor
from .receipt_agrements_processor import ReceiptAgrementsProcessor
from .registry_stats_processor import RegistryStatsProcessor
from .registry_transporter_stats_processor import RegistryTransporterStatsProcessor
from .same_emitter_recipient_table_processor import SameEmitterRecipientTableProcessor
from .ssd_processor import SSDProcessor
from .storage_stats_processor import StorageStatsProcessor
from .traceability_interruptions_processor import TraceabilityInterruptionsProcessor
from .transporter_bordereaux_stats_processor import TransporterBordereauxStatsProcessor
from .waste_flows_table_processor import WasteFlowsTableProcessor
from .waste_is_dangerous_statements_processor import WasteIsDangerousStatementsProcessor
from .waste_processing_without_icpe_rubrique_processor import WasteProcessingWithoutICPERubriqueProcessor

__all__ = [
    "BsdaWorkerStatsProcessor",
    "BsdCanceledTableProcessor",
    "BsdRefusedTableProcessor",
    "BsdStatsProcessor",
    "FollowedWithPNTTDTableProcessor",
    "GistridStatsProcessor",
    "ICPEItemsProcessor",
    "IncineratorOutgoingWasteProcessor",
    "IntermediaryBordereauxStatsProcessor",
    "LinkedCompaniesProcessor",
    "PrivateIndividualsCollectionsTableProcessor",
    "QuantityOutliersTableProcessor",
    "ReceiptAgrementsProcessor",
    "RegistryStatsProcessor",
    "RegistryTransporterStatsProcessor",
    "SameEmitterRecipientTableProcessor",
    "SSDProcessor",
    "StorageStatsProcessor",
    "TraceabilityInterruptionsProcessor",
    "TransporterBordereauxStatsProcessor",
    "WasteFlowsTableProcessor",
    "WasteIsDangerousStatementsProcessor",
    "WasteProcessingWithoutICPERubriqueProcessor",
]
