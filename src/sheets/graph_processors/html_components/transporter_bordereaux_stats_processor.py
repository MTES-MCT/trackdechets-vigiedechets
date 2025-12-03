from datetime import datetime
from itertools import chain
from typing import Dict

import polars as pl

from sheets.utils import format_number_str

from ...constants import BSDA, BSDASRI, BSDD, BSDD_NON_DANGEROUS, BSFF, BSVHU


class TransporterBordereauxStatsProcessor:
    """Component that compute statistics about number of bordereaux as transporter company and corresponding quantities.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    transporters_data_df: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau transported data.
        Correspond to the new way of managing transporters in Trackdéchets.
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    data_date_interval: tuple
        Date interval to filter data.
    packagings_data_df : pl.LazyFrame | None
        Optional parameter that represents a LazyFrame containing data about BSFF packagings.
    """

    def __init__(
        self,
        company_siret: str,
        transporters_data_df: Dict[str, pl.LazyFrame],  # Handling new multi-modal Trackdéchets feature
        bs_data_dfs: Dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
        packagings_data_df: pl.LazyFrame | None = None,
    ) -> None:
        self.company_siret = company_siret
        self.transporters_data_df = transporters_data_df
        self.bs_data_dfs = bs_data_dfs
        self.data_date_interval = data_date_interval
        self.packagings_data_df = packagings_data_df

        self.transported_bordereaux_stats = {
            BSDD: {},
            BSDD_NON_DANGEROUS: {},
            BSDA: {},
            BSFF: {},
            BSDASRI: {},
            BSVHU: {},
        }

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it to be displayed."""
        transporter_data_dfs = self.transporters_data_df
        bs_data_dfs = self.bs_data_dfs

        for bs_type, df in chain(transporter_data_dfs.items(), bs_data_dfs.items()):
            df = df.filter(
                pl.col("sent_at").is_between(*self.data_date_interval)
                & (pl.col("transporter_company_siret") == self.company_siret)
            )

            id_col = "bs_id" if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDA, BSFF] else "id"

            num_bordereaux = df.select(pl.col(id_col).n_unique()).collect().item()
            quantity = df.select(pl.col("quantity_received").sum()).collect().item()
            self.transported_bordereaux_stats[bs_type]["count"] = num_bordereaux
            self.transported_bordereaux_stats[bs_type]["quantity"] = format_number_str(quantity, 2)

    def _check_data_empty(self) -> bool:
        if all((e is None) or (e == {}) for e in self.transported_bordereaux_stats.values()):
            return True

        return False

    def build(self):
        self._preprocess_bs_data()

        data = {}
        if not self._check_data_empty():
            data = self.transported_bordereaux_stats

        return data
