from datetime import datetime

import polars as pl

from sheets.utils import format_number_str


class TraceabilityInterruptionsProcessor:
    """Component that displays list of declared traceability interruptions.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bsdd_data: LazyFrame
        LazyFrame containing BSDD data.
    waste_codes_df: LazyFrame
        LazyFrame containing list of waste codes with their descriptions.
    data_date_interval : tuple[datetime, datetime]
        Represents the date range for which the data is being processed.
        It consists of two `datetime` objects, the start date and the end date.
    """

    def __init__(
        self,
        company_siret: str,
        bsdd_data: pl.LazyFrame,
        waste_codes_df: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret

        self.bsdd_data = bsdd_data
        self.waste_codes_df = waste_codes_df
        self.data_date_interval = data_date_interval

        self.preprocessed_data = None

    def _preprocess_data(self) -> None:
        if self.bsdd_data is None:
            return

        df_filtered = self.bsdd_data.filter(
            pl.col("no_traceability")
            & (pl.col("recipient_company_siret") == self.company_siret)
            & pl.col("received_at").is_between(*self.data_date_interval)
        )

        # Handle quantity refused
        df_filtered = df_filtered.with_columns(
            pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)
        )

        # Quantity and count are computed by waste code
        df_grouped = df_filtered.group_by("waste_code").agg(
            pl.col("quantity_received").sum().alias("quantity"), pl.col("id").count().alias("count")
        )

        # Data is enriched with waste description from the waste nomenclature
        final_df = df_grouped.join(
            self.waste_codes_df,
            left_on="waste_code",
            right_on="code",
            how="left",
            validate="1:1",
        )

        final_df = final_df.with_columns(
            pl.col("quantity").map_elements(lambda x: format_number_str(x, precision=2), return_dtype=pl.String)
        ).sort("quantity", descending=True)

        self.preprocessed_data = final_df.collect()

    def _check_data_empty(self) -> bool:
        if (self.preprocessed_data is None) or (len(self.preprocessed_data) == 0):
            return True

        return False

    def _add_stats(self) -> list:
        stats = []

        for e in self.preprocessed_data.iter_rows(named=True):
            row = {
                "waste_code": e["waste_code"],
                "count": e["count"],
                "quantity": e["quantity"],
                "description": e["description"],
            }
            stats.append(row)
        return stats

    def build(self) -> list:
        self._preprocess_data()

        if not self._check_data_empty():
            return self._add_stats()
        return []
