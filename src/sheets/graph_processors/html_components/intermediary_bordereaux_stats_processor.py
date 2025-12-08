from datetime import datetime
from typing import Dict

import polars as pl

from sheets.utils import format_number_str

from ...constants import BSDA, BSDASRI, BSDD, BSDD_NON_DANGEROUS


class IntermediaryBordereauxStatsProcessor:
    """Component that compute statistics about number of bordereaux as "eco-organisme" and corresponding quantities.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    transporters_data_df: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau transported data.
        Correspond to the new way of managing transporters in Trackdéchets.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        transporters_data_df: Dict[str, pl.LazyFrame],  # Handling new multi-modal Trackdéchets feature
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.bs_data_dfs = bs_data_dfs
        self.transporters_data_df = transporters_data_df
        self.data_date_interval = data_date_interval

        self.bordereaux_stats = {
            BSDD: {},
            BSDD_NON_DANGEROUS: {},
            BSDA: {},
            BSDASRI: {},
        }

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it to be displayed."""
        bs_data_dfs = self.bs_data_dfs

        for bs_type, df in bs_data_dfs.items():
            if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDA]:
                transport_df = self.transporters_data_df.get(bs_type)

                if transport_df is None:
                    continue

                df = df.select(pl.selectors.exclude("sent_at"))  # To avoid column duplication with transport data

                df = df.join(
                    transport_df.select(["bs_id", "sent_at"]),
                    left_on="id",
                    right_on="bs_id",
                    how="left",
                    validate="1:m",
                )

            df = df.filter(
                pl.col("sent_at").is_between(*self.data_date_interval)
                & (pl.col("eco_organisme_siret") == self.company_siret)
            )
            df = df.unique("id")

            num_bordereaux = df.select(pl.col("id").n_unique()).collect().item()

            # handle quantity refused
            if bs_type in [BSDD, BSDD_NON_DANGEROUS]:
                df = df.with_columns(
                    (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                        "quantity_received"
                    )
                )

            quantity = df.unique("id").select(pl.col("quantity_received").sum()).collect().item()
            self.bordereaux_stats[bs_type]["count"] = format_number_str(num_bordereaux, 0)
            self.bordereaux_stats[bs_type]["quantity"] = format_number_str(quantity, 2)

    def _check_data_empty(self) -> bool:
        if all((e is None) or (e == {}) for e in self.bordereaux_stats.values()):
            return True

        return False

    def build(self):
        self._preprocess_bs_data()

        data = {}
        if not self._check_data_empty():
            data = self.bordereaux_stats

        return data
