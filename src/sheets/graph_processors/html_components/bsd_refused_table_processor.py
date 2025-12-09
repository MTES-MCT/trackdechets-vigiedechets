from datetime import datetime
from typing import Dict

import polars as pl

from sheets.utils import format_number_str

from ...constants import BSFF


class BsdRefusedTableProcessor:
    """Component that displays an exhaustive tables with the list of 'bordereaux' that have been refused.

    Parameters
    ----------

    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    data_date_interval : tuple[datetime, datetime]
        Represents the date range for which the data is being processed.
        It consists of two `datetime` objects, the start date and the end date.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        packagings_data_df: pl.LazyFrame,
        waste_codes_df: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.bs_data_dfs = bs_data_dfs
        self.packagings_data_df = packagings_data_df
        self.waste_codes_df = waste_codes_df
        self.data_date_interval = data_date_interval

        self.preprocessed_df = pl.DataFrame()

    def _compute_bsff_quantities(self, bsff_df: pl.LazyFrame) -> pl.LazyFrame:
        if self.packagings_data_df is None:
            bsff_df = bsff_df.with_columns(
                pl.lit(0.0).alias("quantity_received"),
                pl.lit(0.0).alias("quantity_refused"),
            )
            return bsff_df

        df = bsff_df.select(pl.selectors.exclude("quantity_received"))
        df = df.join(
            self.packagings_data_df.group_by("bsff_id").agg(
                pl.col("acceptation_weight").sum().round(3), pl.col("weight").sum().round(3)
            ),
            left_on="id",
            right_on="bsff_id",
        ).rename({"acceptation_weight": "quantity_received", "weight": "quantity_refused"})

        return df

    def _preprocess_data(self) -> None:
        """
        Preprocess the data to display the list of 'bordereaux' that have been refused.
        """
        columns_to_take = [
            "readable_id",
            "refused_at",
            "emitter_company_siret",
            "recipient_company_siret",
            "waste_code",
            "waste_name",
            "quantity_emitted",
            "quantity_refused",
            "refusal_reason",
        ]

        dfs_processed = []

        for bs_type, df in self.bs_data_dfs.items():
            refused_bs_df = df.filter(
                (pl.col("recipient_company_siret") == self.company_siret)
                & (pl.col("status") == "REFUSED")
                & pl.col("received_at").is_between(*self.data_date_interval)
            ).with_columns(
                pl.col("received_at").dt.strftime("%d/%m/%Y %H:%M").alias("refused_at"),
                pl.col("waste_details_quantity").alias("quantity_emitted"),
            )

            if bs_type == BSFF:
                if self.packagings_data_df is None:
                    refused_bs_df = refused_bs_df.with_columns(
                        pl.lit(0.0).alias("quantity_emitted"),
                        pl.lit(0.0).alias("quantity_refused"),
                        pl.lit("").alias("refusal_reason"),
                    )
                else:
                    # We keep only BSFF "refused" for which all packagings are also refused.
                    # If at least one packaging has a different refusal reason, we consider it partially refused and we don't show it in this appendix.
                    refused_bs_df = (
                        refused_bs_df.join(
                            self.packagings_data_df.group_by("bsff_id").agg(
                                (pl.col("acceptation_status") == "REFUSED").alias("is_packaged_refused"),
                                (pl.col("refusal_reason")).alias("refusal_reasons"),
                            ),
                            left_on="id",
                            right_on="bsff_id",
                        )
                        .filter(pl.col("is_packaged_refused").list.all())
                        .with_columns(
                            pl.when(pl.col("refusal_reasons").is_null())
                            .then(pl.lit(""))
                            .otherwise(pl.col("refusal_reasons").list.join(" | "))
                            .alias("refusal_reason"),
                            pl.lit(0.0).alias("quantity_refused"),
                        )
                    )

            schema = refused_bs_df.collect_schema().names()

            # BSDASRI, BSVHU, BSFF do not have waste name
            if "waste_name" not in schema:
                refused_bs_df = refused_bs_df.join(
                    self.waste_codes_df.select("code", pl.col("description").alias("waste_name")),
                    left_on="waste_code",
                    right_on="code",
                    how="left",
                )
                pass

            # fill emitter_company_siret if it is null or empty
            # with particulier if the emitter is a private individual
            # with n/a if the emitter is not a private individual or if we do not know
            if "emitter_is_private_individual" in schema:
                refused_bs_df = refused_bs_df.with_columns(
                    pl.when(
                        (
                            (pl.col("emitter_company_siret").is_null() | (pl.col("emitter_company_siret") == ""))
                            & (pl.col("emitter_is_private_individual"))
                        )
                    )
                    .then(pl.lit("PARTICULIER"))
                    .otherwise(pl.col("emitter_company_siret"))
                    .alias("emitter_company_siret")
                )
            refused_bs_df = refused_bs_df.with_columns(
                pl.coalesce([pl.col("emitter_company_siret"), pl.lit("N/A")])
                .cast(pl.String)
                .alias("emitter_company_siret")
            )

            refused_bs_df = (
                refused_bs_df.with_columns(
                    pl.coalesce([pl.col("refusal_reason"), pl.lit("")]).cast(pl.String).alias("refusal_reason")
                )
                .with_columns(
                    pl.col("quantity_emitted")
                    .map_elements(lambda x: format_number_str(x, 2, "N/A"), return_dtype=pl.String)
                    .alias("quantity_emitted"),
                    pl.col("quantity_refused")
                    .map_elements(lambda x: format_number_str(x, 2, "N/A"), return_dtype=pl.String)
                    .alias("quantity_refused"),
                )
                .select(columns_to_take)
            )
            dfs_processed.append(refused_bs_df)

        if dfs_processed:
            concat_df = pl.concat(dfs_processed, how="diagonal")
            self.preprocessed_df = concat_df.collect()

    def _check_empty_data(self) -> bool:
        if self.preprocessed_df.is_empty():
            return True
        return False

    def build_context(self):
        data = self.preprocessed_df
        return data.to_dicts()

    def build(self):
        self._preprocess_data()

        data = {}
        if not self._check_empty_data():
            data = self.build_context()

        return data
