from datetime import datetime

import polars as pl


class PrivateIndividualsCollectionsTableProcessor:
    """Component that displays a list of private individuals where waste have been picked up.
    Only for BSDA data.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bsda_data_df: LazyFrame
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    bsda_transporters_data_df : LazyFrame
        LazyFrames containing information about the transported BSDA waste.
    data_date_interval : tuple[datetime, datetime]
        Represents the date range for which the data is being processed.
        It consists of two `datetime` objects, the start date and the end date.
    """

    def __init__(
        self,
        company_siret: str,
        bsda_data_df: pl.LazyFrame,
        bsda_transporters_data_df: pl.LazyFrame | None,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.bsda_transporters_data_df = bsda_transporters_data_df
        self.bsda_data_df = bsda_data_df
        self.data_date_interval = data_date_interval

        self.preprocessed_data = None

    def _preprocess_data(self) -> None:
        df = self.bsda_data_df
        transport_df = self.bsda_transporters_data_df

        if (df is None) or (transport_df is None):
            return

        # Handling multimodal
        df = df.with_columns(pl.selectors.exclude("sent_at"))  # To avoid column duplication with transport data

        df = df.join(
            transport_df.select(["bs_id", "sent_at", "transporter_company_siret"]),
            left_on="id",
            right_on="bs_id",
            how="left",
            validate="1:m",
        )

        df = df.group_by("id").agg(
            pl.col("emitter_is_private_individual").max(),
            pl.col("recipient_company_siret").max(),
            pl.col("worker_company_siret").max(),
            pl.col("emitter_company_name").max(),
            pl.col("emitter_company_address").max(),
            pl.col("worksite_name").max(),
            pl.col("worksite_address").max(),
            pl.col("waste_code").max(),
            pl.col("waste_name").max(),
            pl.col("quantity_received").max(),
            pl.col("sent_at").min(),
            pl.col("received_at").min(),
        )

        filtered_df = (
            df.filter(
                (
                    (pl.col("recipient_company_siret") == self.company_siret)
                    | (pl.col("worker_company_siret") == self.company_siret)
                )
                & pl.col("emitter_is_private_individual")
                & pl.col("sent_at").is_between(*self.data_date_interval)
            )
            .sort("sent_at")
            .with_columns(
                pl.col("sent_at").dt.strftime("%d/%m/%Y %H:%M"),
                pl.col("received_at").dt.strftime("%d/%m/%Y %H:%M"),
            )
        )

        filtered_df = filtered_df.collect()
        if len(filtered_df) > 0:
            self.preprocessed_data = filtered_df

    def _check_data_empty(self) -> bool:
        if self.preprocessed_data is None:
            return True

        return False

    def _add_stats(self) -> list:
        stats = []

        for e in self.preprocessed_data.iter_rows(named=True):
            row = {
                "id": e["id"],
                "recipient_company_siret": e["recipient_company_siret"],
                "worker_company_siret": e["worker_company_siret"],
                "emitter_company_name": e["emitter_company_name"],
                "emitter_company_address": e["emitter_company_address"],
                "worksite_name": e["worksite_name"],
                "worksite_address": e["worksite_address"],
                "waste_code": e["waste_code"],
                "waste_name": e["waste_name"],
                "quantity": e["quantity_received"],
                "sent_at": e["sent_at"],
                "received_at": e["received_at"],
            }
            stats.append(row)
        return stats

    def build(self) -> list:
        self._preprocess_data()

        if not self._check_data_empty():
            return self._add_stats()
        return []
