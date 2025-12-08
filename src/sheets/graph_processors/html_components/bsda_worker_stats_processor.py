from datetime import datetime, timedelta

import polars as pl

from sheets.utils import format_number_str


class BsdaWorkerStatsProcessor:
    """Component that compute stats related to worker companies.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bsda_data_df: LazyFrame
        LazyFrame containing BSDA data.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        bsda_data_df: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.bsda_data_df = bsda_data_df
        self.data_date_interval = data_date_interval
        self.company_siret = company_siret

        self.bsda_worker_stats = {
            "signed_producer": None,
            "signed_worker": None,  # and producer
            "signed_transporter": None,  # and worker + producer
            "received": None,
            "processed": None,
            "signed_vs_processed_ratio": None,
            "avg_processing_time_from_emission": None,  # Between signature of producer data and processing date
            "max_processing_time_from_emission": None,  # Between signature of producer data and processing date
            "max_processing_time_from_sending": None,
            "avg_processing_time_from_sending": None,
        }

    def _preprocess_data(self) -> None:
        siret = self.company_siret

        df = self.bsda_data_df

        df = df.filter(pl.col("worker_company_siret") == siret)

        self.bsda_worker_stats["signed_producer"] = len(
            df.filter(pl.col("emitter_emission_signature_date").is_between(*self.data_date_interval)).collect()
        )
        self.bsda_worker_stats["signed_worker"] = len(
            df.filter(
                pl.col("emitter_emission_signature_date").is_between(*self.data_date_interval)
                & pl.col("worker_work_signature_date").is_between(*self.data_date_interval)
            ).collect()
        )
        self.bsda_worker_stats["signed_transporter"] = len(
            df.filter(
                pl.col("emitter_emission_signature_date").is_between(*self.data_date_interval)
                & pl.col("worker_work_signature_date").is_between(*self.data_date_interval)
                & pl.col("sent_at").is_between(*self.data_date_interval)
            ).collect()
        )
        self.bsda_worker_stats["received"] = len(
            df.filter(pl.col("received_at").is_between(*self.data_date_interval)).collect()
        )
        self.bsda_worker_stats["processed"] = len(
            df.filter(pl.col("processed_at").is_between(*self.data_date_interval)).collect()
        )

        if self.bsda_worker_stats["signed_worker"] > 0:
            self.bsda_worker_stats["signed_vs_processed_ratio"] = format_number_str(
                100 * self.bsda_worker_stats["processed"] / self.bsda_worker_stats["signed_worker"],
                2,
            )

        df_filtered = df.filter(
            pl.col("processed_at").is_between(*self.data_date_interval)
            & pl.col("emitter_emission_signature_date").is_between(*self.data_date_interval)
            & pl.col("worker_work_signature_date").is_between(*self.data_date_interval)
        )
        times_to_process_from_emission = df_filtered.select(
            (pl.col("processed_at") - pl.col("emitter_emission_signature_date")).alias("time_to_process")
        )
        max_time_to_process_from_emission: timedelta | None = (
            times_to_process_from_emission.select(pl.col("time_to_process").max()).collect().item()
        )
        avg_time_to_process_from_emission: timedelta | None = (
            times_to_process_from_emission.select(pl.col("time_to_process").mean()).collect().item()
        )

        if max_time_to_process_from_emission is not None:
            self.bsda_worker_stats["max_processing_time_from_emission"] = format_number_str(
                max_time_to_process_from_emission.total_seconds() / (3600 * 24), 2
            )

        if avg_time_to_process_from_emission is not None:
            self.bsda_worker_stats["avg_processing_time_from_emission"] = format_number_str(
                avg_time_to_process_from_emission.total_seconds() / (3600 * 24)
            )

        df_filtered = df.filter(
            pl.col("processed_at").is_between(*self.data_date_interval)
            & pl.col("sent_at").is_between(*self.data_date_interval)
            & pl.col("worker_work_signature_date").is_between(*self.data_date_interval)
        )
        times_to_process_from_sending = df_filtered.select(
            (pl.col("processed_at") - pl.col("sent_at")).alias("time_to_process")
        )
        max_time_to_process_from_sending: timedelta | None = (
            times_to_process_from_sending.select(pl.col("time_to_process").max()).collect().item()
        )
        avg_time_to_process_from_sending: timedelta | None = (
            times_to_process_from_sending.select(pl.col("time_to_process").mean()).collect().item()
        )

        if max_time_to_process_from_sending is not None:
            self.bsda_worker_stats["max_processing_time_from_sending"] = format_number_str(
                max_time_to_process_from_sending.total_seconds() / (3600 * 24), 2
            )

        if avg_time_to_process_from_sending is not None:
            self.bsda_worker_stats["avg_processing_time_from_sending"] = format_number_str(
                avg_time_to_process_from_sending.total_seconds() / (3600 * 24)
            )

    def _check_empty_data(self) -> bool:
        if all(e in [None, 0, "0"] for e in self.bsda_worker_stats.values()):
            return True

        return False

    def build(self):
        self._preprocess_data()

        res = {}

        if not self._check_empty_data():
            res = self.bsda_worker_stats
        return res
