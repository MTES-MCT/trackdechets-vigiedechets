from datetime import datetime
from typing import Dict

import polars as pl

from ...constants import BSDA, BSDD, BSDD_NON_DANGEROUS


class SameEmitterRecipientTableProcessor:
    """Component that displays an exhaustive tables with the
    list of 'bordereaux' that have the same company
    as emitter and recipient along with a worksite address.

    Parameters
    ----------
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    transporters_data_df : Dict[str, pl.LazyFrame]
        Dictionary that contains LazyFrames related to transporters. Each key in the "Bordereau type" (BSDD, BSDA...)
        and the corresponding value is a polars LazyFrame containing information about the transported waste.
    data_date_interval : tuple[datetime, datetime]
        Represents the date range for which the data is being processed.
        It consists of two `datetime` objects, the start date and the end date.
    """

    def __init__(
        self,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        transporters_data_dfs: Dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.bs_data_dfs = bs_data_dfs
        self.transporters_data_dfs = transporters_data_dfs
        self.data_date_interval = data_date_interval

        self.preprocessed_df = pl.DataFrame()

    def _preprocess_data(self) -> None:
        # This case only works on BSDD and BSDA so we filter others type of "bordereaux"
        dfs_to_process = {
            bs_type: df for bs_type, df in self.bs_data_dfs.items() if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDA]
        }

        columns_to_take = [
            "id",
            "readable_id",
            "sent_at",
            "received_at",
            "quantity_received",
            "waste_code",
            "waste_name",
            "worksite_name",
            "worksite_address",
            "emitter_company_siret",
            "recipient_company_siret",
        ]
        dfs_processed = []

        for bs_type, df in dfs_to_process.items():
            transport_df = self.transporters_data_dfs.get(bs_type)

            if (df is None) or (transport_df is None):
                continue

            columns_to_drop = ["sent_at", "transporter_company_siret"]

            # Handling multimodal
            df = df.select(pl.selectors.exclude(columns_to_drop))  # To avoid column duplication with transport data

            transport_df_columns_to_take = ["bs_id", "sent_at", "transporter_company_siret"]

            df = df.join(
                transport_df.select(transport_df_columns_to_take),
                left_on="id",
                right_on="bs_id",
                how="left",
                validate="1:m",
            )

            df = df.group_by("id").agg(
                pl.col(c).min() if c in ["sent_at", "received_at"] else pl.col(c).max()
                for c in columns_to_take
                if c in df.collect_schema().names() and not c == "id"
            )

            if bs_type == BSDA:
                df = df.with_columns(pl.col("id").alias("readable_id"))

            same_emitter_recipient_df = (
                df.filter(
                    (pl.col("emitter_company_siret") == pl.col("recipient_company_siret"))
                    & pl.col("worksite_address").is_not_null()
                    & pl.col("sent_at").is_between(*self.data_date_interval)
                )
                .select(columns_to_take)
                .with_columns(
                    pl.col("sent_at").dt.strftime("%d/%m/%Y %H:%M"),
                    pl.col("received_at").dt.strftime("%d/%m/%Y %H:%M"),
                )
            )

            dfs_processed.append(same_emitter_recipient_df)

        if dfs_processed:
            self.preprocessed_df = pl.concat(dfs_processed, how="diagonal").collect()

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
