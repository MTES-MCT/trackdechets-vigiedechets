from datetime import datetime

import polars as pl

from sheets.constants import BSDD

BSDD_FIELD_PAIRS = [
    ("waste_details_code", "initial_waste_details_code", "Code déchet"),
    ("waste_details_name", "initial_waste_details_name", "Nom du déchet"),
    ("quantity_received", "initial_quantity_received", "Quantité reçue (t)"),
    ("processing_operation_done", "initial_processing_operation_done", "Code opération de traitement"),
    ("waste_details_quantity", "initial_waste_details_quantity", "Quantité estimée (t)"),
    ("recipient_cap", "initial_recipient_cap", "CAP destinataire"),
    ("destination_operation_mode", "initial_destination_operation_mode", "Mode de traitement"),
    ("waste_acceptation_status", "initial_waste_acceptation_status", "Statut d'acceptation"),
    ("quantity_refused", "initial_quantity_refused", "Quantité refusée (t)"),
    ("waste_refusal_reason", "initial_waste_refusal_reason", "Motif de refus"),
    ("waste_details_pop", "initial_waste_details_pop", "Déchet POP"),
]

BSDA_FIELD_PAIRS = [
    ("waste_code", "initial_waste_code", "Code déchet"),
    ("waste_material_name", "initial_waste_material_name", "Dénomination du matériau"),
    ("destination_reception_weight", "initial_destination_reception_weight", "Quantité reçue (t)"),
    ("destination_operation_code", "initial_destination_operation_code", "Code opération de traitement"),
    ("destination_cap", "initial_destination_cap", "CAP"),
    ("destination_operation_mode", "initial_destination_operation_mode", "Mode de traitement"),
    ("waste_pop", "initial_waste_pop", "Déchet POP"),
]


class BsdAutoApprovedRevisionTableProcessor:
    """Component that displays revisions auto-approved without third-party validation.

    This covers BSDD revisions (emitter is private individual or OMI ship) and
    BSDA revisions (emitter is private individual with no work company), identified
    by the absence of a linked revision_request_approval record.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed.
    auto_approved_revision_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame
        containing the auto-approved revision data.
    data_date_interval : tuple[datetime, datetime]
        Represents the date range for which the data is being processed.
    """

    def __init__(
        self,
        company_siret: str,
        auto_approved_revision_dfs: dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.auto_approved_revision_dfs = auto_approved_revision_dfs
        self.data_date_interval = data_date_interval
        self.rows: list[dict] = []

    def _normalize_emitter_siret(self, row: dict) -> str:
        omi_number = row.get("emitter_company_omi_number") or ""
        if omi_number:
            return "N/A (navire OMI)"
        if row.get("emitter_is_private_individual"):
            return "N/A (particulier)"
        siret = row.get("emitter_company_siret") or ""
        return siret if siret else "N/A"

    def _preprocess_data(self) -> None:
        if not self.auto_approved_revision_dfs:
            return

        for bs_type, df in self.auto_approved_revision_dfs.items():
            filtered = (
                df.with_columns(
                    pl.col("updated_at").dt.convert_time_zone(time_zone="Europe/Paris").alias("updated_at_paris")
                )
                .filter(pl.col("updated_at_paris").is_between(*self.data_date_interval))
                .with_columns(pl.col("updated_at_paris").dt.strftime("%d/%m/%Y %H:%M").alias("updated_at_str"))
                .collect()
            )

            if len(filtered) == 0:
                continue

            field_pairs = BSDD_FIELD_PAIRS if bs_type == BSDD else BSDA_FIELD_PAIRS

            for row in filtered.iter_rows(named=True):
                emitter_siret = self._normalize_emitter_siret(row)
                recipient_siret = row.get("recipient_company_siret") or "N/A"
                readable_id = row.get("readable_id") or row["bs_id"]

                for current_col, initial_col, label in field_pairs:
                    current_val = row.get(current_col)
                    initial_val = row.get(initial_col)

                    if current_val is None:
                        continue
                    if current_val == initial_val:
                        continue

                    self.rows.append(
                        {
                            "id": row["bs_id"],
                            "readable_id": readable_id,
                            "updated_at": row["updated_at_str"],
                            "emitter_company_siret": emitter_siret,
                            "recipient_company_siret": recipient_siret,
                            "comment": row.get("comment") or "",
                            "field_name": label,
                            "previous_value": str(initial_val) if initial_val is not None else "",
                            "new_value": str(current_val) if current_val is not None else "",
                        }
                    )

        self.rows.sort(key=lambda r: r["updated_at"])

    def build(self) -> list[dict]:
        self._preprocess_data()
        return self.rows
