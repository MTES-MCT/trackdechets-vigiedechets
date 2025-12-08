from datetime import datetime
from typing import Dict

import polars as pl

from sheets.utils import format_number_str


class FollowedWithPNTTDTableProcessor:
    """Component that displays an exhaustive tables of BSDD followed by PNTTD.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
        Only BSDD and BSDD non dangerous.
    data_date_interval: tuple
        Date interval to filter data.
    waste_codes_df: LazyFrame
        LazyFrame containing list of waste codes with their descriptions. It is the waste nomenclature.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
        waste_codes_df: pl.LazyFrame,
    ) -> None:
        self.bs_data_dfs = bs_data_dfs
        self.data_date_interval = data_date_interval
        self.waste_codes_df = waste_codes_df
        self.company_siret = company_siret

        self.preprocessed_df = None

    def _preprocess_data(self) -> None:
        siret = self.company_siret

        dfs_to_concat = [df for df in self.bs_data_dfs.values() if df is not None]

        if len(dfs_to_concat) == 0:
            self.preprocessed_df = pl.DataFrame()
            return

        df: pl.LazyFrame = pl.concat(dfs_to_concat, how="diagonal")

        df = df.filter(
            (pl.col("recipient_company_siret") == siret)
            & (pl.col("status") == "FOLLOWED_WITH_PNTTD")
            & pl.col("processed_at").is_between(*self.data_date_interval)
        )

        df = df.with_columns(
            pl.when(
                (
                    pl.col("next_destination_company_siret").is_null()
                    | (pl.col("next_destination_company_siret") == "")
                ).not_()
            )
            .then("next_destination_company_siret")
            .otherwise("next_destination_company_vat_number")
            .alias("foreign_org_id"),
            (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                "quantity_received"
            ),  # Handle quantity refused
        )

        # We compute the quantity by waste codes
        df_grouped = df.group_by(
            [
                "foreign_org_id",
                "waste_code",
                "next_destination_processing_operation",
            ]
        ).agg(
            pl.col("quantity_received").sum().alias("quantity"),
            pl.col("next_destination_company_country").max().alias("destination_country"),
        )
        # We add the waste code description from the waste nomenclature
        final_df = df_grouped.join(
            self.waste_codes_df,
            left_on="waste_code",
            right_on="code",
            how="left",
            validate="m:1",
        )

        company_names = df.group_by("foreign_org_id").agg(
            pl.col("next_destination_company_name").max().alias("destination_name")
        )

        final_df = final_df.join(company_names, on="foreign_org_id")

        final_df = (
            final_df.with_columns(
                pl.col("quantity").map_elements(lambda x: format_number_str(x, 2), return_dtype=pl.String),
                pl.col("description").fill_null(""),
            )
            .select(
                [
                    "foreign_org_id",
                    "destination_name",
                    "destination_country",
                    "waste_code",
                    "description",
                    "next_destination_processing_operation",
                    "quantity",
                ]
            )
            .sort(["foreign_org_id", "waste_code"])
        )

        self.preprocessed_df = final_df.collect()

    def _check_empty_data(self) -> bool:
        if self.preprocessed_df is None:
            return True

        if len(self.preprocessed_df) == 0:
            return True

        return False

    def build_context(self):
        return self.preprocessed_df.to_dicts()

    def build(self):
        self._preprocess_data()

        res = {}

        if not self._check_empty_data():
            res = self.build_context()
        return res
