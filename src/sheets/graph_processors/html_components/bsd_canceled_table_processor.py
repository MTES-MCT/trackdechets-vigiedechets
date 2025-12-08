from datetime import datetime
from typing import Dict

import polars as pl


class BsdCanceledTableProcessor:
    """Component that displays an exhaustive tables with the list of 'bordereaux' that have been canceled.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    bs_revised_data: LazyFrame
        Dict with key being the 'bordereau' type and values the LazyFrame containing the associated revision data.
    data_date_interval : tuple[datetime, datetime]
        Represents the date range for which the data is being processed.
        It consists of two `datetime` objects, the start date and the end date.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        bs_revised_data: Dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.bs_data_dfs = bs_data_dfs
        self.data_date_interval = data_date_interval
        self.bs_revised_data = bs_revised_data
        self.company_siret = company_siret

        self.preprocessed_df = pl.DataFrame()

    def _preprocess_data(self) -> None:
        if not self.bs_revised_data:
            return

        dfs = []
        for bs_type, revised_data_df in self.bs_revised_data.items():
            # Cancellation events are stored in revisions
            cancellations = revised_data_df.filter(
                pl.col("is_canceled")
                & pl.col("updated_at")
                .dt.convert_time_zone(time_zone="Europe/Paris")
                .is_between(*self.data_date_interval)
            )

            bs_data = self.bs_data_dfs[bs_type]

            # Columns that will be displayed in the output table
            columns_to_take = [
                "bs_id",  # Will correspond to the 'bordereau' id after merge
                "quantity_received",
                "emitter_company_siret",
                "recipient_company_siret",
                "waste_code",
                "updated_at",
                "comment",
            ]

            schema = bs_data.collect_schema().names()
            # Human-friendly id is stored in the readable_id column in the case of BSDDs
            if "readable_id" in schema:
                columns_to_take.append("readable_id")

            # BSDASRI does not have waste name
            if "waste_name" in schema:
                columns_to_take.append("waste_name")

            # Handle quantity refused
            if "quantity_refused" in schema:
                columns_to_take.append("quantity_refused")

            # fill emitter_company_siret if it is null or empty
            # with particulier if the emitter is a private individual
            # with n/a if the emitter is not a private individual or if we do not know
            if "emitter_is_private_individual" in schema:
                bs_data = bs_data.with_columns(
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
            bs_data = bs_data.with_columns(
                pl.when((pl.col("emitter_company_siret").is_null() | (pl.col("emitter_company_siret") == "")))
                .then(pl.lit("N/A"))
                .otherwise(pl.col("emitter_company_siret"))
                .alias("emitter_company_siret")
            )

            # Join cancellations with bs_data to get bordereau details including emitter_company_siret
            temp_df = cancellations.join(
                bs_data,
                left_on="bs_id",
                right_on="id",
                how="inner",
            )

            # Ensure emitter_company_siret is present and not null after join
            # This handles cases where the join might not preserve the column correctly
            if "emitter_company_siret" in temp_df.collect_schema().names():
                temp_df = temp_df.with_columns(
                    pl.coalesce([pl.col("emitter_company_siret"), pl.lit("N/A")])
                    .cast(pl.String)
                    .alias("emitter_company_siret")
                )
            else:
                # If emitter_company_siret is missing, add it (shouldn't happen but handle gracefully)
                temp_df = temp_df.with_columns(pl.lit("N/A").alias("emitter_company_siret"))

            temp_df = temp_df.select(columns_to_take)
            temp_df = temp_df.rename({"bs_id": "id"}, strict=False)
            dfs.append(temp_df)

        if dfs:
            self.preprocessed_df = (
                pl.concat(dfs, how="diagonal")
                .sort("updated_at")
                .with_columns(pl.col("updated_at").dt.strftime("%d/%m/%Y %H:%M"))
                .collect()
            )

    def _check_empty_data(self) -> bool:
        if len(self.preprocessed_df) == 0:
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
