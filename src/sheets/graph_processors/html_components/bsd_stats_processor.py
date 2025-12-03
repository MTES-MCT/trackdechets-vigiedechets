import numbers
from datetime import datetime
from itertools import chain

import polars as pl

from sheets.utils import format_number_str

from ...constants import BSDASRI, BSDD, BSDD_NON_DANGEROUS, BSFF


class BsdStatsProcessor:
    """Component that displays aggregated data about 'bordereaux' and estimations of the onsite waste stock.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data: LazyFrame
        LazyFrame containing data for a given 'bordereau' type.
    quantity_variables_names: list of str
        The names of the variables to use to compute quantity statistics.
        For example : ["quantity_received","volume"] to compute statistics for both variables.
    bs_revised_data: LazyFrame
        LazyFrame containing list of revised 'bordereaux' for a given 'bordereau' type.
    packagings_data:
        For BSFF data, packagings dataset to be able to compute stats at packaging level.
    """

    def __init__(
        self,
        company_siret: str,
        bs_type: str,
        bs_data: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
        quantity_variables_names: list[str] = ["quantity_received"],
        bs_revised_data: pl.LazyFrame | None = None,
        packagings_data: pl.LazyFrame | None = None,
    ) -> None:
        self.company_siret = company_siret
        self.bs_type = bs_type
        self.bs_data = bs_data
        self.data_date_interval = data_date_interval
        self.quantity_variables_names = self._validate_quantity_variables_names(
            quantity_variables_names, packagings_data
        )
        self.bs_revised_data = bs_revised_data
        self.packagings_data = packagings_data

        # Initialization of dicts that will hold the different computed statistics
        keys = [
            "total",
            "archived",
            "processed_in_more_than_one_month_count",
            "processed_in_more_than_one_month_avg_processing_time",
            "avg_processing_time",
        ]
        if self.packagings_data is not None:
            keys.extend(
                [
                    "total_packagings",
                    "processed_in_more_than_one_month_packagings_count",
                    "processed_in_more_than_one_month_packagings_avg_processing_time",
                    "avg_processing_time",
                ]
            )

        self.emitted_bs_stats = {key: None for key in keys}
        self.received_bs_stats = {key: None for key in keys}

        self.pending_revisions_count = 0
        self.revised_bs_count = 0

        # Quantities stats is two level deep as it will store the statistics for each
        # chosen quantity variables
        self.quantities_stats = {
            key: {
                "total_quantity_incoming": None,
                "total_quantity_outgoing": None,
                "bar_size_incoming": None,
                "bar_size_outgoing": None,
            }
            for key in self.quantity_variables_names
        }

        self.weight_volume_ratio = None

    @staticmethod
    def _validate_quantity_variables_names(quantity_variables_names, packagings_data):
        allowed_quantity_variables_names = [
            "quantity_received",
            "acceptation_weight",
            "volume",
        ]

        clean_quantity_variables_names = [e for e in quantity_variables_names if e in allowed_quantity_variables_names]

        # Allows to handle the case when there is no packagings data but there is BSFF data
        if packagings_data is None:
            clean_quantity_variables_names = [
                e if e != "acceptation_weight" else "quantity_received" for e in clean_quantity_variables_names
            ]

        return list(set(clean_quantity_variables_names))

    def _check_data_empty(self) -> bool:
        # If all values after preprocessing are empty, then output data will be empty
        if all(
            (e is None) or (e == 0) or (e == "N/A")
            for e in chain(self.emitted_bs_stats.values(), self.received_bs_stats.values())
        ):
            return True

        return False

    def _preprocess_general_statistics(self, bs_emitted_data: pl.LazyFrame, bs_received_data: pl.LazyFrame) -> None:
        # For incoming and outgoing data, we compute different statistics
        # about the 'bordereaux'.
        # `target` is the destination in each result dictionary
        # where to store the computed value.
        for target, to_process, to_process_packagings in [
            (self.emitted_bs_stats, bs_emitted_data, self.packagings_data),
            (self.received_bs_stats, bs_received_data, self.packagings_data),
        ]:
            df = to_process

            if self.bs_type == BSFF:
                if to_process_packagings is None:
                    # Case when there is BSFFs but no packagings info
                    continue
                df = (
                    to_process.select(["id", "status", "received_at"])
                    .join(
                        to_process_packagings.filter(pl.col("acceptation_status") == "ACCEPTED").select(
                            ["bsff_id", "operation_date", "acceptation_weight"]
                        ),
                        left_on="id",
                        right_on="bsff_id",
                        how="left",
                        validate="1:m",
                    )
                    .sort(
                        "operation_date", descending=False, nulls_last=True
                    )  # Used to capture the date of the last processed packaging or null if there is at least one packaging not processed
                    .group_by("id", maintain_order=True)
                    .agg(
                        pl.col("status").max(),
                        pl.col("received_at").max(),
                        pl.col("operation_date").first().alias("processed_at"),
                    )
                )

            df = df.collect()
            # total number of 'bordereaux' emitted/received
            target["total"] = len(df)

            # total number of 'bordereaux' that are considered as 'archived' (end of traceability)
            target["archived"] = len(
                df.filter(
                    pl.col("status").is_in(
                        [
                            "PROCESSED",
                            "REFUSED",
                            "NO_TRACEABILITY",
                            "FOLLOWED_WITH_PNTTD",
                            "INTERMEDIATELY_PROCESSED",
                        ]
                    )
                )
            )

            avg_processing_time = df.select(
                (pl.col("processed_at") - pl.col("received_at")).dt.total_seconds().mean()
            ).item()

            target["avg_processing_time"] = (
                f"{(avg_processing_time / (24 * 3600)):.1f}j" if avg_processing_time else "N/A"
            )

            # LazyFrame holding all the 'bordereaux' that have been
            # processed in more than one month.
            bs_emitted_processed_in_more_than_one_month = df.filter(
                (pl.col("processed_at") - pl.col("received_at")) > pl.duration(days=30)
            )

            # Total number of bordereaux processed in more than one month
            processed_in_more_than_one_month_count = len(bs_emitted_processed_in_more_than_one_month)

            target["processed_in_more_than_one_month_count"] = processed_in_more_than_one_month_count

            # If there is some 'bordereaux' processed in more than one month,
            # we compute the average processing time.
            if processed_in_more_than_one_month_count:
                res = bs_emitted_processed_in_more_than_one_month.select(
                    (pl.col("processed_at") - pl.col("received_at")).mean().dt.total_seconds()
                ).item() / (24 * 3600)  # Time in seconds is converted in days

                target["processed_in_more_than_one_month_avg_processing_time"] = f"{format_number_str(res, 1)}j"

            # Handle the case of BSFF specific packagings statistics
            if to_process_packagings is not None:
                # Total number of packagings sent/received
                target["total_packagings"] = len(
                    to_process_packagings.filter(
                        pl.col("bsff_id").is_in(df["id"]) & (pl.col("operation_date").is_not_null())
                    ).collect()
                )

                # Merging of BSFF 'bordereaux' data with associated packagings data
                # as we will need the date of reception that is stored at the 'bordereau' level.
                bs_data_with_packagings = to_process.join(
                    to_process_packagings,
                    left_on="id",
                    right_on="bsff_id",
                    validate="1:m",
                    how="left",
                )

                # LazyFrame with all BSFF along with packagings data
                # for packagings that have been processed in more than one month
                bs_data_with_packagings_processed_in_more_than_one_month = bs_data_with_packagings.filter(
                    (pl.col("operation_date") - pl.col("received_at")) > pl.duration(days=30)
                ).collect()

                if len(bs_data_with_packagings_processed_in_more_than_one_month) > 0:
                    # Number of packagings processed in more than one month.
                    target["processed_in_more_than_one_month_packagings_count"] = len(
                        bs_data_with_packagings_processed_in_more_than_one_month
                    )

                    # Average processing times for the packagings processed in more than one month
                    avg_processing_time_more_than_one_month = (
                        bs_data_with_packagings_processed_in_more_than_one_month.select(
                            (pl.col("operation_date") - pl.col("received_at")).mean().dt.total_seconds()
                        ).item()
                        / (24 * 3600)
                    )  # Time in seconds is converted in days

                    target["processed_in_more_than_one_month_packagings_avg_processing_time"] = (
                        f"{avg_processing_time_more_than_one_month:.1f}j"
                    )

        # In case there is any 'bordereaux' revision data, we compute
        # the number of 'bordereaux' that have been revised.
        # NOTE: only revision asked by the current organization are computed.
        bs_revised_data = self.bs_revised_data
        if bs_revised_data is not None:
            bs_revised_data = bs_revised_data.filter(
                pl.col("bs_id").is_in(bs_emitted_data.select("id").collect()["id"].to_list())
                | pl.col("bs_id").is_in(bs_received_data.select("id").collect()["id"].to_list())
            ).collect()

            self.pending_revisions_count = (
                bs_revised_data.filter(pl.col("status") == "PENDING").select(pl.col("id").n_unique()).item()
            )
            self.revised_bs_count = (
                bs_revised_data.filter(pl.col("status") == "ACCEPTED").select(pl.col("bs_id").n_unique()).item()
            )

    def _preprocess_quantities_stats(self, bs_emitted_data: pl.LazyFrame, bs_received_data: pl.LazyFrame) -> None:
        # We iterate over the different variables chosen to compute the statistics
        for key in self.quantities_stats.keys():
            # If there is a packagings_data LazyFrame, then it means that we are
            # computing BSFF statistics, in this case we use the packagings data instead of
            # 'bordereaux' data as quantity information is stored at packaging level
            if self.bs_type == BSFF:
                if self.packagings_data is None:
                    # Case when there is BSFFs but no packagings info
                    continue

                total_quantity_incoming = (
                    bs_received_data.join(self.packagings_data, left_on="id", right_on="bsff_id")
                    .select(pl.col(key).sum())
                    .collect()
                    .item()
                )
                total_quantity_outgoing = (
                    bs_emitted_data.join(self.packagings_data, left_on="id", right_on="bsff_id")
                    .select(pl.col(key).sum())
                    .collect()
                    .item()
                )
            else:
                df_received = bs_received_data
                df_emitted = bs_emitted_data
                if self.bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDASRI]:
                    # Handle quantity refused
                    col_expr = (
                        pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)
                    ).alias("quantity_received")
                    df_received = df_received.with_columns(col_expr)
                    df_emitted = df_emitted.with_columns(col_expr)

                total_quantity_incoming = df_received.select(pl.col(key).sum()).collect().item()
                total_quantity_outgoing = df_emitted.select(pl.col(key).sum()).collect().item()

            self.quantities_stats[key]["total_quantity_incoming"] = total_quantity_incoming
            self.quantities_stats[key]["total_quantity_outgoing"] = total_quantity_outgoing

            incoming_bar_size = 0
            outgoing_bar_size = 0

            if not (total_quantity_incoming == total_quantity_outgoing == 0):
                # The bar sizes are relative to the largest quantity.
                # Size is expressed as percentage of the component width.
                if total_quantity_incoming > total_quantity_outgoing:
                    incoming_bar_size = 100
                    outgoing_bar_size = int(100 * (total_quantity_outgoing / total_quantity_incoming))
                else:
                    incoming_bar_size = int(100 * (total_quantity_incoming / total_quantity_outgoing))
                    outgoing_bar_size = 100
            self.quantities_stats[key]["bar_size_incoming"] = incoming_bar_size
            self.quantities_stats[key]["bar_size_outgoing"] = outgoing_bar_size

        # If both "quantity_received" and "volume" variables have been chosen,
        # then it means that we are computing BSDASRI statistics.
        # In this case we compute the ratio between volume and weight.
        if all(key in self.quantity_variables_names for key in ["quantity_received", "volume"]):
            if (self.quantities_stats["volume"]["total_quantity_incoming"]) > 0:
                self.weight_volume_ratio = (
                    self.quantities_stats["quantity_received"]["total_quantity_incoming"]
                    / self.quantities_stats["volume"]["total_quantity_incoming"]
                )

    def _preprocess_data(self) -> None:
        bs_data = self.bs_data

        bs_emitted_data = bs_data.filter(
            (pl.col("emitter_company_siret") == self.company_siret)
            & (pl.col("sent_at").is_between(*self.data_date_interval))
        )
        bs_received_data = bs_data.filter(
            (pl.col("recipient_company_siret") == self.company_siret)
            & (pl.col("received_at").is_between(*self.data_date_interval))
        )

        self._preprocess_general_statistics(bs_emitted_data, bs_received_data)

        self._preprocess_quantities_stats(bs_emitted_data, bs_received_data)

    def build_context(self):
        # We use the format_number_str only on variables that holds
        # quantity values.
        ctx = {
            "emitted_bs_stats": {
                k: (format_number_str(v, 0) if isinstance(v, numbers.Number) else v)
                for k, v in self.emitted_bs_stats.items()
            },
            "received_bs_stats": {
                k: (format_number_str(v, 0) if isinstance(v, numbers.Number) else v)
                for k, v in self.received_bs_stats.items()
            },
            "pending_revisions_count": format_number_str(self.pending_revisions_count, precision=0),
            "revised_bs_count": format_number_str(self.revised_bs_count, precision=0),
            # quantities_stats is two level deep so we need to use a nested
            # dict comprehension loop.
            "quantities_stats": {
                ok: {
                    k: (format_number_str(v, 2) if k in ["total_quantity_incoming", "total_quantity_outgoing"] else v)
                    for k, v in ov.items()
                }
                for ok, ov in self.quantities_stats.items()
            },
            # We multiply the weight to get kilograms instead of tons for the weight_volume_ratio
            "weight_volume_ratio": format_number_str(self.weight_volume_ratio * 1000, 2)
            if self.weight_volume_ratio is not None
            else None,
        }

        return ctx

    def build(self):
        self._preprocess_data()

        data = {}
        if not self._check_data_empty():
            data = self.build_context()
        return data
