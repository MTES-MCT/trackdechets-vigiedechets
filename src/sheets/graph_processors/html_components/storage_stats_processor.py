from datetime import datetime
from typing import Dict

import polars as pl

from sheets.utils import format_number_str

from ...constants import BS_TYPES_WITH_MULTIMODAL_TRANSPORT, BSDD_NON_DANGEROUS


class StorageStatsProcessor:
    """Component that displays waste stock on site by waste codes (TOP 4) and total stock in tons.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    waste_codes_df: LazyFrame
        LazyFrame containing list of waste codes with their descriptions.
    data_date_interval : tuple[datetime, datetime]
        Represents the date range for which the data is being processed.
        It consists of two `datetime` objects, the start date and the end date.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        transporters_data_df: Dict[str, pl.LazyFrame],
        waste_codes_df: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret

        self.bs_data_dfs = bs_data_dfs
        self.transporters_data_df = transporters_data_df
        self.waste_codes_df = waste_codes_df
        self.data_date_interval = data_date_interval

        self.stock_by_waste_code = None
        self.total_stock = None

    def _preprocess_data(self):
        siret = self.company_siret

        dfs_to_concat = []
        for bs_type, df in self.bs_data_dfs.items():
            if (df is None) or (bs_type == BSDD_NON_DANGEROUS):
                continue

            if bs_type in BS_TYPES_WITH_MULTIMODAL_TRANSPORT:
                transport_df = self.transporters_data_df.get(bs_type)
                if transport_df is None:
                    continue

                agg_exprs = [
                    pl.col("emitter_company_siret").max(),
                    pl.col("recipient_company_siret").max(),
                    pl.col("waste_code").max(),
                    pl.col("quantity_received").max(),
                    pl.col("sent_at").min(),
                    pl.col("received_at").min(),
                ]
                if "quantity_refused" in df.collect_schema().names():
                    agg_exprs.append(
                        pl.col("quantity_refused").max(),
                    )

                df_to_concat = (
                    df.select(pl.selectors.exclude("sent_at"))
                    .join(transport_df, left_on="id", right_on="bs_id", suffix="_transport", validate="1:m")
                    .group_by("id")
                    .agg(*agg_exprs)
                )
                dfs_to_concat.append(df_to_concat)

            else:
                # Keep only necessary columns for later processing
                columns_needed = [
                    "id",
                    "emitter_company_siret",
                    "recipient_company_siret",
                    "waste_code",
                    "quantity_received",
                    "sent_at",
                    "received_at",
                    "quantity_refused",
                ]
                df_to_concat = df.select([c for c in columns_needed if c in df.collect_schema().names()])
                dfs_to_concat.append(df_to_concat)

        if len(dfs_to_concat) > 0:
            df = pl.concat(dfs_to_concat, how="diagonal")
            # Handle quantity refused
            if "quantity_refused" in df.collect_schema().names():
                df = df.with_columns(pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0))

            emitted_mask = (pl.col("emitter_company_siret") == siret) & pl.col("sent_at").is_between(
                *self.data_date_interval
            )
            received_mask = (pl.col("recipient_company_siret") == siret) & pl.col("received_at").is_between(
                *self.data_date_interval
            )

            emitted = df.filter(emitted_mask).group_by("waste_code").agg(pl.col("quantity_received").sum())
            received = df.filter(received_mask).group_by("waste_code").agg(pl.col("quantity_received").sum())

            # Index wise sum (index being the waste codes)
            # to compute the theoretical stock of waste
            # (difference between incoming and outgoing quantities)
            stock_by_waste_code = (
                emitted.join(received, on="waste_code", how="full", validate="1:1")
                .with_columns(
                    (
                        pl.col("quantity_received_right").fill_nan(0).fill_null(0)
                        - pl.col("quantity_received").fill_nan(0).fill_null(0)
                    ).alias("quantity_received")
                )  # emitted - received
                .select(
                    [pl.coalesce(pl.col("waste_code"), pl.col("waste_code_right")), "quantity_received"]
                )  # We can discard temp columns from received df
                .filter(
                    (pl.col("quantity_received") > 0) & pl.col("waste_code").is_not_null()
                )  # Only positive differences are kept
                .sort("quantity_received", descending=True)
            )

            total_stock = format_number_str(
                stock_by_waste_code.select(pl.col("quantity_received").sum()).collect().item(), precision=1
            )

            stock_by_waste_code = stock_by_waste_code.with_columns(
                pl.col("quantity_received").map_elements(
                    lambda x: format_number_str(x, precision=2), return_dtype=pl.String
                )
            )

            # Data is enriched with waste description from the waste nomenclature
            stock_by_waste_code = stock_by_waste_code.join(
                self.waste_codes_df,
                left_on="waste_code",
                right_on="code",
                how="left",
                validate="1:1",
            )
            stock_by_waste_code.with_columns(pl.col("description").fill_null(""))

            self.stock_by_waste_code = stock_by_waste_code.collect()
            self.total_stock = total_stock

    def _check_data_empty(self) -> bool:
        if len(self.stock_by_waste_code) == 0:
            return True

        return False

    def _add_stats(self):
        stored_waste = []

        for row in self.stock_by_waste_code.head(4).iter_rows(named=True):
            stored_waste.append(
                {
                    "quantity_received": row["quantity_received"],
                    "code": str(row["waste_code"]),
                    "description": row["description"],
                }
            )
        return {"stored_waste": stored_waste, "total_stock": self.total_stock}

    def build(self):
        self._preprocess_data()

        data = {}
        if not self._check_data_empty():
            data = self._add_stats()
        return data
