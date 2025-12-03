from datetime import datetime

import polars as pl

from sheets.utils import format_number_str


class SSDProcessor:
    """Component that aggregate data to show a table of SSD quantities by waste code.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    ssd_data: LazyFrame
        LazyFrame containing list of ssd statements.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        ssd_data: pl.LazyFrame | None,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.ssd_data = ssd_data
        self.data_date_interval = data_date_interval

        self.preprocessed_data = pl.DataFrame()

    def _preprocess_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it to be displayed."""
        ssd_data_df = self.ssd_data

        if ssd_data_df is None:
            return

        ssd_data = ssd_data_df.filter(
            (pl.col("siret") == self.company_siret) & (pl.col("dispatch_date").is_between(*self.data_date_interval))
        )

        dfs = []
        for quantity_colname in ["weight_value", "volume"]:
            ssd_data_agg = ssd_data.group_by("waste_code").agg(
                pl.col(quantity_colname).sum().alias("quantity"), pl.col("waste_description").max()
            )
            ssd_data_agg = ssd_data_agg.with_columns(
                pl.lit("t" if quantity_colname == "weight_value" else "m³").alias("unit")
            )
            ssd_data_agg = ssd_data_agg.sort(["waste_code", "unit"])
            dfs.append(ssd_data_agg)

        if len(dfs) > 0:
            final_df: pl.LazyFrame = pl.concat(dfs, how="diagonal")
            self.preprocessed_data = final_df.collect()

    def _check_data_empty(self) -> bool:
        if len(self.preprocessed_data) == 0:
            return True

        return False

    def _serialize_stats(self) -> list[dict]:
        res = []

        for row in self.preprocessed_data.iter_rows(named=True):
            res.append(
                {
                    "waste_code": row["waste_code"],
                    "waste_name": row["waste_description"],
                    "quantity": format_number_str(row["quantity"], 2),
                    "unit": row["unit"],
                }
            )

        return res

    def build(self):
        self._preprocess_data()

        data = {}
        if not self._check_data_empty():
            data = self._serialize_stats()

        return data
