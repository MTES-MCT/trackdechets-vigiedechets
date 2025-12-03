from datetime import datetime
from typing import Dict

import polars as pl

from sheets.utils import format_number_str


class RegistryTransporterStatsProcessor:
    """Component that compute statistics about number of RDNTS statements as transporter company and corresponding quantities.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    registry_data: dict
        Dict with key being the registry type and values the LazyFrame containing the statements data.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        registry_data: Dict[str, pl.LazyFrame | None],
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.registry_data = registry_data
        self.data_date_interval = data_date_interval

        self.transported_statements_stats = {
            "ndw_incoming": {},
            "ndw_outgoing": {},
            "excavated_land_incoming": {},
            "excavated_land_outgoing": {},
        }

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it to be displayed."""

        registry_data = self.registry_data

        for key, date_col in [
            ("ndw_incoming", "reception_date"),
            ("ndw_outgoing", "dispatch_date"),
            ("excavated_land_incoming", "reception_date"),
            ("excavated_land_outgoing", "dispatch_date"),
        ]:
            df = registry_data[key]
            if df is None:
                continue

            df = (
                df.filter(
                    pl.col(date_col).is_between(*self.data_date_interval)
                    & (pl.col("transporters_org_ids").list.contains(self.company_siret))
                )
                .select(
                    pl.col("id").n_unique().alias("num_statements"),
                    pl.col("weight_value").sum().alias("mass_quantity"),
                    pl.col("volume").sum().alias("volume_quantity"),
                )
                .collect()
            )

            if len(df) > 0:
                num_statements = df["num_statements"].item()
                mass_quantity = df["mass_quantity"].item()
                volume_quantity = df["volume_quantity"].item()

                if num_statements is not None:
                    self.transported_statements_stats[key]["count"] = num_statements
                if mass_quantity is not None:
                    self.transported_statements_stats[key]["mass_quantity"] = format_number_str(mass_quantity, 2)
                if volume_quantity is not None:
                    self.transported_statements_stats[key]["volume_quantity"] = format_number_str(volume_quantity, 2)

    def _check_data_empty(self) -> bool:
        if all(
            (e is None) or (e == {}) or (all(y == 0 for y in e.values()))
            for e in self.transported_statements_stats.values()
        ):
            return True

        return False

    def build(self):
        self._preprocess_bs_data()

        data = {}
        if not self._check_data_empty():
            data = self.transported_statements_stats

        return data
