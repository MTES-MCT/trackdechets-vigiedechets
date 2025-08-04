import numbers
from datetime import datetime, timedelta
from itertools import chain
from typing import Dict
from zoneinfo import ZoneInfo

import polars as pl

from sheets.utils import format_number_str

from ..constants import BS_TYPES_WITH_MULTIMODAL_TRANSPORT, BSDA, BSDASRI, BSDD, BSDD_NON_DANGEROUS, BSFF, BSVHU

# classes returning a context to be rendered in a non-plotly template


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
        ]
        if self.packagings_data is not None:
            keys.extend(
                [
                    "total_packagings",
                    "processed_in_more_than_one_month_packagings_count",
                    "processed_in_more_than_one_month_packagings_avg_processing_time",
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
            (e is None) or (e == 0) for e in chain(self.emitted_bs_stats.values(), self.received_bs_stats.values())
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

                    res = bs_data_with_packagings_processed_in_more_than_one_month.select(
                        (pl.col("operation_date") - pl.col("received_at")).mean().dt.total_seconds()
                    ).item() / (24 * 3600)  # Time in seconds is converted in days

                    target["processed_in_more_than_one_month_packagings_avg_processing_time"] = f"{res:.1f}j"

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


class WasteFlowsTableProcessor:
    """Component that displays an exhaustive tables with input and output wastes classified by waste codes.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    transporters_data_df : Dict[str, pl.LazyFrame]
        Dictionary that contains LazyFrames related to transporters. Each key in the "Bordereau type" (BSDD, BSDA...)
        and the corresponding value is a polars LazyFrame containing information about the transported waste.
    registry_data: dict of LazyFrames
        LazyFrame containing registry statements data.
    data_date_interval : tuple[datetime, datetime]
        Represents the date range for which the data is being processed.
        It consists of two `datetime` objects, the start date and the end date.
    waste_codes_df: LazyFrame
        LazyFrame containing list of waste codes with their descriptions. It is the waste nomenclature.
    packagings_data : pl.LazyFrame | None
        Optional parameter that represents a LazyFrame containing data about BSFF packagings.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        transporters_data_df: Dict[str, pl.LazyFrame],  # Handling new multi-modal Trackdéchets feature
        registry_data: dict[str, pl.LazyFrame | None],
        data_date_interval: tuple[datetime, datetime],
        waste_codes_df: pl.LazyFrame,
        packagings_data: pl.LazyFrame | None = None,
    ) -> None:
        self.bs_data_dfs = bs_data_dfs
        self.transporters_data_df = transporters_data_df
        self.registry_data = registry_data
        self.data_date_interval = data_date_interval
        self.waste_codes_df = waste_codes_df
        self.packagings_data = packagings_data
        self.company_siret = company_siret

        self.preprocessed_df = None

    def _preprocess_bs_data(self) -> pl.LazyFrame | None:
        siret = self.company_siret

        dfs_to_concat = []
        for bs_type, df in self.bs_data_dfs.items():
            if df is None:
                continue

            # Handling multimodal
            if bs_type in BS_TYPES_WITH_MULTIMODAL_TRANSPORT:
                transport_df = self.transporters_data_df.get(bs_type)

                if transport_df is not None:
                    if len(df.collect()) > 0:
                        df = df.select(
                            pl.selectors.exclude("sent_at")
                        )  # To avoid column duplication with transport data
                        if bs_type == BSFF:
                            if self.packagings_data is not None:
                                # Quantity is taken from packagings data in case of BSFF
                                df = df.join(
                                    self.packagings_data.select(["bsff_id", "acceptation_weight", "acceptation_date"]),
                                    left_on="id",
                                    right_on="bsff_id",
                                    validate="1:m",
                                )
                                df = df.rename({"acceptation_weight": "quantity_received"})

                                # data is re-aggregated at 'bordereau' granularity to match other 'bordereaux' dfs granularity
                                df = df.group_by("id").agg(
                                    pl.col("emitter_company_siret").max(),
                                    pl.col("recipient_company_siret").max(),
                                    pl.col("received_at").min(),
                                    pl.col("waste_code").max(),
                                    pl.col("quantity_received").sum(),
                                )
                            else:
                                # If there is no packagings data, we can't get the quantity
                                continue

                        transport_columns_to_take = ["bs_id", "sent_at", "transporter_company_siret"]

                        validation = "m:m"  # Due to merging with packaging before
                        if (not bs_type == BSFF) or (
                            self.packagings_data is None
                        ):  # BSFF stores quantity in packagings data
                            validation = "1:m"

                        if bs_type in [BSDD, BSDD_NON_DANGEROUS]:
                            # Handle quantity refused
                            df = df.with_columns(
                                (
                                    pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)
                                ).alias("quantity_received")
                            )

                        df = df.join(
                            transport_df.select(transport_columns_to_take),
                            left_on="id",
                            right_on="bs_id",
                            how="left",
                            validate=validation,
                        )

                        df = df.group_by("id").agg(
                            pl.col("emitter_company_siret").max(),
                            pl.col("recipient_company_siret").max(),
                            pl.col("transporter_company_siret").max(),
                            pl.col("sent_at").min(),
                            pl.col("received_at").min(),
                            pl.col("waste_code").max(),
                            pl.col("quantity_received").max(),
                        )
                    else:
                        df = transport_df
            elif bs_type == "BSDASRI":
                df = df.with_columns(
                    (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                        "quantity_received"
                    )
                )
            dfs_to_concat.append(df)

        if len(dfs_to_concat) == 0:
            return

        df: pl.LazyFrame = pl.concat(dfs_to_concat, how="diagonal")

        # We create a column to differentiate incoming waste from
        # outgoing and transported waste.
        df = df.with_columns(pl.lit(None).alias("flow_status"))

        # We determine each "flow type", a 'bordereau' can have several flow status (e.g a company that emit and also transport)
        dfs_to_concat = []
        for siret_key, date_key, flow_type in [
            ("emitter_company_siret", "sent_at", "outgoing"),
            ("recipient_company_siret", "received_at", "incoming"),
            ("transporter_company_siret", "sent_at", "transported"),
        ]:
            if (siret_key in df.columns) and (date_key in df.columns):
                temp_df = df.filter(
                    (pl.col(siret_key) == siret) & (pl.col(date_key).is_between(*self.data_date_interval))
                ).with_columns(pl.lit(flow_type).alias("flow_status"))
                dfs_to_concat.append(temp_df)

        df: pl.LazyFrame = pl.concat(dfs_to_concat, how="diagonal").drop_nulls("flow_status")

        # We compute the quantity by waste codes and incoming/outgoing/transported categories
        df_grouped = (
            df.group_by(["waste_code", "flow_status"])
            .agg(pl.col("quantity_received").sum())
            .with_columns(pl.lit("t").alias("unit"), pl.col("quantity_received").round(3))
        )

        return df_grouped

    def _preprocess_registry_data(self) -> pl.LazyFrame | None:
        # Deletes unecessary timezone from date interval

        # If there is registry data, we add it to the LazyFrame
        dfs_to_group = []
        for key, date_col in [
            (
                "ndw_incoming",
                "reception_date",
            ),
            (
                "ndw_outgoing",
                "dispatch_date",
            ),
            (
                "excavated_land_incoming",
                "reception_date",
            ),
            (
                "excavated_land_outgoing",
                "dispatch_date",
            ),
        ]:
            df_registry = self.registry_data.get(key)

            if df_registry is not None:
                dfs_to_concat = []

                for unit, col in [("t", "weight_value"), ("m³", "volume")]:
                    registry_agg_data = (
                        df_registry.filter(
                            pl.col(date_col).is_between(*self.data_date_interval)
                            & (pl.col("siret") == self.company_siret)
                        )
                        .rename({col: "quantity_received"})
                        .group_by(["waste_code"])
                        .agg(pl.col("quantity_received").sum())
                        .drop_nulls()
                        .with_columns(pl.lit(unit).alias("unit"))
                        .filter(pl.col("quantity_received") > 0)
                    )
                    dfs_to_concat.append(registry_agg_data)

                registry_grouped_data = pl.concat(dfs_to_concat, how="diagonal").with_columns(
                    pl.lit("incoming" if (date_col == "reception_date") else "outgoing").alias("flow_status")
                )
                dfs_to_group.append(registry_grouped_data)

                # Transport data
                dfs_to_concat = []

                for unit, quantity_col in [("t", "quantity_received"), ("m³", "volume")]:
                    rename_mapping = {"weight_value": "quantity_received"}
                    if quantity_col == "volume":
                        rename_mapping = {"volume": "quantity_received"}

                    registry_transporter_weight_data = (
                        df_registry.filter(
                            pl.col(date_col).is_between(*self.data_date_interval)
                            & pl.col("transporters_org_ids").list.contains(self.company_siret)
                        )
                        .rename(rename_mapping)
                        .group_by("waste_code")
                        .agg(pl.col("quantity_received").sum())
                        .drop_nulls()
                        .with_columns(pl.lit(unit).alias("unit"))
                        .filter(pl.col("quantity_received") > 0)
                    )
                    dfs_to_concat.append(registry_transporter_weight_data)

                if len(dfs_to_concat) > 0:
                    registry_grouped_data = pl.concat(dfs_to_concat, how="diagonal")

                    registry_grouped_data = registry_grouped_data.with_columns(
                        pl.lit(
                            "transported_incoming" if (date_col == "reception_date") else "transported_outgoing"
                        ).alias("flow_status")
                    )
                    dfs_to_group.append(registry_grouped_data)

        res = None
        if len(dfs_to_group) > 0:
            res = pl.concat(dfs_to_group, how="diagonal")

        return res

    def _preprocess_data(self):
        bs_grouped_data = self._preprocess_bs_data()
        registry_grouped_data = self._preprocess_registry_data()

        df_grouped = pl.LazyFrame()
        match (bs_grouped_data, registry_grouped_data):
            case (None, None):
                return
            case (pl.LazyFrame(), pl.LazyFrame()):
                df_grouped = pl.concat([bs_grouped_data, registry_grouped_data], how="diagonal")
            case (df, None) | (None, df):
                df_grouped = df
            case _:
                raise ValueError()

        # We add the waste code description from the waste nomenclature
        final_df = df_grouped.join(
            self.waste_codes_df,
            left_on="waste_code",
            right_on="code",
            how="left",
            validate="m:1",
        )

        final_df = final_df.filter(pl.col("quantity_received") > 0)
        final_df = final_df.with_columns(pl.col("description").fill_null(""))
        final_df = final_df.group_by(
            ["waste_code", "flow_status", "unit"]
        ).agg(
            pl.col("description").max(), pl.col("quantity_received").sum()
        )  # A waste code can be present in different registries or bordereaux, this final aggregation aims to have only one value for a tuple ()"waste_code", "flow_status", "unit")
        final_df = final_df.select(["waste_code", "description", "flow_status", "quantity_received", "unit"]).sort(
            by=["waste_code", "flow_status", "unit"], descending=[False, False, True]
        )
        final_df = final_df.with_columns(
            pl.col("quantity_received").map_elements(lambda x: format_number_str(x, 3), return_dtype=pl.String)
        )

        self.preprocessed_df = final_df.collect()

    def _check_empty_data(self) -> bool:
        if self.preprocessed_df is None:
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

            schema = bs_data.columns
            # Human-friendly id is stored in the readable_id column in the case of BSDDs
            if "readable_id" in schema:
                columns_to_take.append("readable_id")

            # BSDASRI does not have waste name
            if "waste_name" in schema:
                columns_to_take.append("waste_name")

            # Handle quantity refused
            if "quantity_refused" in schema:
                columns_to_take.append("quantity_refused")

            temp_df = cancellations.join(
                bs_data,
                left_on="bs_id",
                right_on="id",
            )

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
                if c in df.columns and not c == "id"
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
                if "quantity_refused" in df.columns:
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
                dfs_to_concat.append(df)

        if len(dfs_to_concat) > 0:
            df = pl.concat(dfs_to_concat, how="diagonal")
            # Handle quantity refused
            if "quantity_refused" in df.columns:
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


class ICPEItemsProcessor:
    """Component that displays list of ICPE authorized items.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    icpe_data: LazyFrame
        LazyFrame containing list of ICPE authorized items
    """

    def __init__(
        self,
        company_siret: str,
        icpe_data: pl.LazyFrame | None,
    ) -> None:
        self.company_siret = company_siret
        self.icpe_data = icpe_data

        self.preprocessed_df = None

    def _preprocess_data(self):
        df = self.icpe_data

        if df is None:
            return

        df = df.with_columns(
            pl.col("quantite").map_elements(lambda x: format_number_str(x, precision=3), return_dtype=pl.String)
        )

        df = df.sort("rubrique")

        self.preprocessed_df = df.collect()

    def build_context(self) -> list[dict]:
        data = self.preprocessed_df

        # Handle "nan" textual values not being converted to JSON null
        data = data.with_columns(pl.col("quantite").replace("nan", None))
        return data.to_dicts()

    def _check_empty_data(self) -> bool:
        if self.preprocessed_df is None or len(self.preprocessed_df) == 0:
            return True

        return False

    def build(self):
        self._preprocess_data()

        data = {}
        if not self._check_empty_data():
            data = self.build_context()

        return data


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


class WasteIsDangerousStatementsProcessor:
    """Component that displays list of wastes tracked
    without dangerous waste code but with the "waste_is_dangerous" option enabled.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bsdd_data: LazyFrame
        LazyFrame containing bsdd data.
    bsdd_transporters_data : LazyFrame
        LazyFrames containing information about the transported BSDD waste.
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
        bsdd_transporters_data: pl.LazyFrame | None,
        waste_codes_df: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret

        self.bsdd_data = bsdd_data
        self.bsdd_transporters_data = bsdd_transporters_data
        self.waste_codes_df = waste_codes_df
        self.data_date_interval = data_date_interval

        self.preprocessed_data = None

    def _preprocess_data(self) -> None:
        if (self.bsdd_data is None) or (self.bsdd_transporters_data is None):
            return

        df = self.bsdd_data
        transport_df = self.bsdd_transporters_data

        # Handling multimodal
        df = df.select(pl.selectors.exclude("sent_at"))  # To avoid column duplication with transport data

        df = df.join(
            transport_df.select(["bs_id", "sent_at", "transporter_company_siret"]),
            left_on="id",
            right_on="bs_id",
            how="left",
            validate="1:m",
        )

        df = df.group_by("id").agg(
            pl.col("is_dangerous").max(),
            pl.col("emitter_company_siret").max(),
            pl.col("waste_code").max(),
            pl.col("sent_at").min(),
            pl.col("quantity_received").max(),
            pl.col("quantity_refused").max(),
        )

        df_filtered = df.filter(
            pl.col("is_dangerous")
            & (pl.col("emitter_company_siret") == self.company_siret)
            & (pl.col("waste_code").str.contains(r".*\*$").not_())
            & (pl.col("sent_at").is_between(*self.data_date_interval))
        )

        # Handle quantity refused
        df_filtered = df_filtered.with_columns(
            pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)
        )

        df_grouped = df_filtered.group_by("waste_code").agg(
            pl.col("quantity_received").sum().alias("quantity"), pl.col("id").count().alias("count")
        )

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


class ReceiptAgrementsProcessor:
    """Component that displays informations about the company receipts and agreements.

    Parameters
    ----------
    receipts_agreements_data : dict
        Dict with keys being the name of the receipt/agreement and values being LazyFrames
        with one line per receipt/agreement (usually there is only one receipt for a receipt type for an establishment but
        there might be more).
    """

    def __init__(self, receipts_agreements_data: Dict[str, pl.LazyFrame]) -> None:
        self.receipts_agreements_data = {k: v.collect() for k, v in receipts_agreements_data.items()}

    def _check_data_empty(self) -> bool:
        if len(self.receipts_agreements_data) == 0:
            return True

        return False

    def build(self):
        res = []
        for name, data in self.receipts_agreements_data.items():
            for line in data.iter_rows(named=True):
                validity_str = ""
                if "validity_limit" in line.keys():
                    # todo: utcnow
                    if line["validity_limit"] < datetime.now(tz=ZoneInfo("Europe/Paris")):
                        validity_str = f"expiré depuis le {line['validity_limit']:%d/%m/%Y}"
                    else:
                        validity_str = f"valide jusqu'au {line['validity_limit']:%d/%m/%Y}"
                res.append(
                    {
                        "name": name,
                        "number": line["receipt_number"],
                        "validity_str": validity_str,
                    }
                )

        return res


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


class QuantityOutliersTableProcessor:
    """Component that displays a list of bordereaux with outliers values on quantity.

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
    packagings_data_df : pl.LazyFrame | None
        Optional parameter that represents a LazyFrame containing data about BSFF packagings.
    """

    def __init__(
        self,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        transporters_data_df: Dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
        packagings_data_df: pl.LazyFrame | None = None,
    ) -> None:
        self.bs_data_dfs = bs_data_dfs
        self.transporters_data_df = transporters_data_df
        self.packagings_data_df = packagings_data_df
        self.data_date_interval = data_date_interval

        self.preprocessed_data = None

    def get_quantity_outliers(
        self,
        df: pl.LazyFrame,
        bs_type: str,
        transporters_df: pl.LazyFrame | None,
        packagings_data_df: pl.LazyFrame | None,
    ) -> pl.LazyFrame | None:
        """Get lines from 'bordereau' LazyFrame with inconsistent received quantity.
        The rules to identify outliers in received quantity are business rules and may be tweaked in the future.

        Parameters
        ----------
        df : LazyFrame
            LazyFrame with 'bordereau' data.
        bs_type : str
            Name of the 'bordereau' (BSDD, BSDD_NON_DANGEROUS, BSDA, BSFF, BSVHU or BSDASRI).

        Returns
        -------
        LazyFrame
            LazyFrame with lines with received quantity outliers removed or None if no data.
        """
        df_quantity_outliers = pl.LazyFrame()
        if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDA, BSFF] and (transporters_df is not None):
            # In this case we use transporter data

            # Old 'bordereaux' data could contain sent_at column, we want to use the one from transport data
            df = df.select(pl.selectors.exclude("sent_at"))

            df_with_transport = df.join(
                transporters_df.select(
                    [
                        "bs_id",
                        "transporter_company_siret",
                        "transporter_transport_mode",
                        "sent_at",
                    ]
                ),
                left_on="id",
                right_on="bs_id",
                how="left",
                validate="1:m",
                suffix="_transport",
            )

            if bs_type == BSFF:
                if packagings_data_df is not None:
                    df_with_transport = df_with_transport.select(pl.selectors.exclude("quantity_received"))
                    df_with_transport = df_with_transport.join(
                        packagings_data_df.group_by("bsff_id").agg(pl.col("acceptation_weight").sum()),
                        left_on="id",
                        right_on="bsff_id",
                    ).rename({"acceptation_weight": "quantity_received"})
                else:
                    return

            df_quantity_outliers = df_with_transport.filter(
                (pl.col("quantity_received") > 40)
                & ((pl.col("transporter_transport_mode") == "ROAD") | pl.col("transporter_transport_mode").is_null())
                & pl.col("sent_at").is_between(*self.data_date_interval)
            ).unique("id")

        elif bs_type == BSDASRI:
            df_quantity_outliers = df.filter(
                (pl.col("quantity_received") > 20)
                & (pl.col("transporter_transport_mode") == "ROAD")
                & (pl.col("sent_at").is_between(*self.data_date_interval))
            )
        elif bs_type == BSVHU:
            df_quantity_outliers = df.filter(
                (pl.col("quantity_received") > 40) & (pl.col("sent_at").is_between(*self.data_date_interval))
            )
        else:
            #
            return
        df_quantity_outliers = df_quantity_outliers.with_columns(
            pl.lit(bs_type if bs_type != BSDD_NON_DANGEROUS else "bsdd").alias("bs_type")
        )
        return df_quantity_outliers

    def _preprocess_data(self) -> None:
        outliers_dfs = []
        for bs_type, df in self.bs_data_dfs.items():
            packagings_data_df = None
            if bs_type == BSFF:
                packagings_data_df = self.packagings_data_df

            transporters_df = self.transporters_data_df.get(bs_type, None)
            df_outliers = self.get_quantity_outliers(df, bs_type, transporters_df, packagings_data_df)

            if df_outliers is not None:
                if bs_type in [BSDD, BSDD_NON_DANGEROUS]:
                    df_outliers = df_outliers.with_columns(pl.col("readable_id").alias("id")).sort("sent_at")

                outliers_dfs.append(df_outliers)

        if outliers_dfs:
            self.preprocessed_data = (
                pl.concat(outliers_dfs, how="diagonal")
                .with_columns(
                    pl.col("sent_at").dt.strftime("%d/%m/%Y %H:%M"),
                    pl.col("received_at").dt.strftime("%d/%m/%Y %H:%M"),
                )
                .collect()
            )

    def _check_data_empty(self) -> bool:
        if self.preprocessed_data is None:
            return True

        return False

    def _add_stats(self) -> list:
        stats = []

        has_quantity_refused = "quantity_refused" in self.preprocessed_data.columns

        for e in self.preprocessed_data.iter_rows(named=True):
            row = {
                "id": e["id"],
                "bs_type": e["bs_type"],
                "emitter_company_siret": e["emitter_company_siret"],
                "transporter_company_siret": e["transporter_company_siret"],
                "recipient_company_siret": e["recipient_company_siret"],
                "waste_code": e["waste_code"],
                "waste_name": e["waste_name"] if e["bs_type"] != "bsvhu" else None,
                "quantity": format_number_str(e["quantity_received"], 1),
                "quantity_refused": format_number_str(e["quantity_refused"], 1) if has_quantity_refused else None,
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


class WasteProcessingWithoutICPERubriqueProcessor:
    """Component that detects when waste is processed without having a 'rubrique' in ICPE data.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    registry_incoming_data: LazyFrame
        LazyFrame containing data for incoming non dangerous waste (from registry).
    icpe_data: pl.LazyFrame
        LazyFrame containing the list of authorized 'rubriques'.
    data_date_interval : tuple[datetime, datetime]
        Represents the date range for which the data is being processed.
        It consists of two `datetime` objects, the start date and the end date.
    packagings_data_df : pl.LazyFrame | None
        Optional parameter that represents a LazyFrame containing data about BSFF packagings.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame | None],
        registry_incoming_data: pl.LazyFrame | None,
        icpe_data: pl.LazyFrame | None,
        data_date_interval: tuple[datetime, datetime],
        packagings_data_df: pl.LazyFrame | None = None,
    ) -> None:
        self.siret = company_siret
        self.bs_data_dfs = bs_data_dfs
        self.registry_incoming_data = registry_incoming_data
        self.icpe_data = icpe_data
        self.data_date_interval = data_date_interval
        self.packagings_data_df = packagings_data_df

        self.preprocessed_data = {
            "dangerous": [],
            "non_dangerous": [],
        }

    def _preprocess_data_multi_rubriques(self) -> None:
        has_2760_1 = False
        has_2760_2 = False
        icpe_data = self.icpe_data

        if icpe_data is not None:
            has_2760_1 = len(icpe_data.filter(pl.col("rubrique") == "2760-1").collect()) > 0
            has_2760_2 = (
                len(icpe_data.filter(pl.col("rubrique").is_in(["2760-2", "2760-2-a", "2760-2-b"])).collect()) > 0
            )

        if not has_2760_1:  # Means no authorization for ICPE 2760-1
            bs_2760_dfs = []
            bsdd_data = self.bs_data_dfs.get(BSDD)

            if bsdd_data is not None:
                bsdd_data_filtered = bsdd_data.filter(
                    (pl.col("recipient_company_siret") == self.siret)
                    & (pl.col("processing_operation_code") == "D5")
                    & (pl.col("processed_at").is_between(*self.data_date_interval))
                )

                bsdd_data_filtered = bsdd_data_filtered.with_columns(pl.lit("BSDD").alias("bs_type"))
                bs_2760_dfs.append(bsdd_data_filtered)

            if not has_2760_2:  # Means no authorization for ICPE 2760-1 NEITHER 2760-2 (BSDA case)
                bsda_data = self.bs_data_dfs[BSDA]

                if bsda_data is not None:
                    bsda_data_filtered = bsda_data.filter(
                        (pl.col("recipient_company_siret") == self.siret)
                        & (pl.col("processing_operation_code") == "D5")
                        & (pl.col("processed_at").is_between(*self.data_date_interval))
                    )
                    bsda_data_filtered = bsda_data_filtered.with_columns(pl.lit("BSDA").alias("bs_type"))
                    bs_2760_dfs.append(bsda_data_filtered)

            if len(bs_2760_dfs) > 0:
                bs_df: pl.LazyFrame = pl.concat(bs_2760_dfs, how="diagonal")

                filter_expr = pl.col("quantity_received") > 0
                if "quantity_refused" in bs_df.columns:
                    filter_expr = (
                        pl.col("quantity_received") - pl.col("quantity_refused").fill_null(0).fill_nan(0)
                    ) > 0

                bs_df = bs_df.filter(filter_expr)

                bs_df = bs_df.collect()  # Creates the list of bordereaux

                if len(bs_df) > 0:
                    total_quantity = bs_df.select(pl.col("quantity_received").sum()).item()
                    if "quantity_refused" in bs_df.columns:
                        total_quantity -= (
                            bs_df.select(pl.col("quantity_refused").sum()).fill_null(0).fill_nan(0).sum().item()
                        )

                    self.preprocessed_data["dangerous"].append(
                        {
                            "missing_rubriques": "2760-1, 2760-2",
                            "num_missing_rubriques": 2,
                            "found_processing_codes": "D5",
                            "num_found_processing_codes": 1,
                            "bs_list": bs_df,
                            "stats": {
                                "total_bs": format_number_str(len(bs_df), 0),  # Total number of bordereaux
                                "total_quantity": format_number_str(total_quantity, 2),  # Total quantity processed
                            },
                        }
                    )

    def _preprocess_data_single_rubrique(self) -> None:
        configs = [
            {
                "rubrique": "2770",
                "data": [
                    (bs_type, df)
                    for bs_type, df in self.bs_data_dfs.items()
                    if bs_type in [BSDD, BSDA, BSFF, BSDASRI, BSVHU]
                ],
                "processing_codes": ["D10", "R1"],
            },
            {
                "rubrique": "2718-1",
                "data": [
                    (bs_type, df) for bs_type, df in self.bs_data_dfs.items() if bs_type in [BSDD, BSDA, BSFF, BSDASRI]
                ],
                "processing_codes": ["D13", "D14", "D15", "R12", "R13", "D9"],
            },
            {
                "rubrique": "2790",
                "data": [
                    (bs_type, df)
                    for bs_type, df in self.bs_data_dfs.items()
                    if bs_type in [BSDD, BSDA, BSFF, BSDASRI, BSVHU]
                ],
                "processing_codes": [
                    "D8",
                    "D9F",
                    "R2",
                    "R3",
                    "R4",
                    "R5",
                    "R6",
                    "R7",
                    "R9",
                ],
            },
        ]

        for config in configs:
            rubrique = config["rubrique"]

            has_rubrique = False
            icpe_data = self.icpe_data
            if icpe_data is not None:
                has_rubrique = len(icpe_data.filter(pl.col("rubrique") == rubrique).collect()) > 0

            if not has_rubrique:
                df_to_process = config["data"]

                bs_filtered_df = self._preprocess_and_filter_bs_list(
                    self.siret,
                    df_to_process,
                    config["processing_codes"],
                    self.data_date_interval,
                    self.packagings_data_df,
                )

                if "quantity_refused" in bs_filtered_df.columns:
                    bs_filtered_df = bs_filtered_df.with_columns(
                        pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)
                    )

                bs_filtered_df.filter(pl.col("quantity_received") > 0)

                bs_filtered_df = bs_filtered_df.collect()
                if len(bs_filtered_df) > 0:
                    found_processing_codes = sorted(
                        bs_filtered_df["processing_operation_code"].unique().drop_nulls().to_list()
                    )
                    self.preprocessed_data["dangerous"].append(
                        {
                            "bs_list": bs_filtered_df,  # Creates the list of bordereaux
                            "missing_rubriques": rubrique,
                            "num_missing_rubriques": 1,
                            "found_processing_codes": ", ".join(found_processing_codes),
                            "num_found_processing_codes": len(found_processing_codes),
                            "stats": {
                                "total_bs": format_number_str(len(bs_filtered_df), 0),  # Total number of bordereaux
                                "total_quantity": format_number_str(
                                    bs_filtered_df["quantity_received"].sum(), 2
                                ),  # Total quantity processed
                            },
                        }
                    )

    def _preprocess_non_dangerous_rubriques(self) -> None:
        registry_data_df = self.registry_incoming_data

        if registry_data_df is None:
            return

        registry_data_df = registry_data_df.filter(
            (pl.col("siret") == self.siret) & pl.col("reception_date").is_between(*self.data_date_interval)
        )

        rubriques_mapping = [
            {
                "rubriques": ["2760-2"],
                "processing_codes": ["D5"],
            },
            {
                "rubriques": ["2771"],
                "processing_codes": [
                    "D10",
                ],
            },
            {
                "rubriques": ["2771", "2791"],
                "processing_codes": [
                    "D9",
                    "R1",
                    "R2",
                    "R5",
                    "R7",
                ],
            },
            {
                "rubriques": ["2791"],
                "processing_codes": [
                    "D8",
                    "R3",
                    "R4",
                    "R8",
                    "R12",
                ],
            },
        ]

        for mapping in rubriques_mapping:
            rubriques = mapping["rubriques"]

            has_rubrique = False
            icpe_data_df = self.icpe_data
            missing_rubriques = rubriques
            if icpe_data_df is not None:
                # Handle 2791 case that can have alinea
                installation_rubriques = icpe_data_df.select(
                    pl.col("rubrique").str.slice(0, 6).str.replace(pattern="^2791.*", value="2791").unique()
                )

                # To handle the case of rubriques with trailing "-a" or trailing "-b", we use only the 6 first characters
                missing_rubriques = set(rubriques) - set(installation_rubriques.collect()["rubrique"].to_list())
                has_rubrique = len(missing_rubriques) == 0

            if has_rubrique:
                continue

            processing_codes = mapping["processing_codes"]

            filtered_registry_data_df = (
                registry_data_df.filter(pl.col("operation_code").is_in(processing_codes))
                .sort("reception_date")
                .collect()
            )

            if len(filtered_registry_data_df) > 0:
                found_processing_codes = sorted(filtered_registry_data_df["operation_code"].unique().to_list())

                self.preprocessed_data["non_dangerous"].append(
                    {
                        "missing_rubriques": ", ".join(missing_rubriques),
                        "num_missing_rubriques": len(missing_rubriques),
                        "found_processing_codes": ", ".join(found_processing_codes),
                        "num_found_processing_codes": len(found_processing_codes),
                        "statements_list": filtered_registry_data_df,  # Creates the list of statements
                        "stats": {
                            "total_statements": format_number_str(
                                len(filtered_registry_data_df), 0
                            ),  # Total number of bordereaux
                            "total_quantity": format_number_str(
                                filtered_registry_data_df["weight_value"].sum(), 2
                            ),  # Total quantity processed
                        },
                    }
                )

    @staticmethod
    def _preprocess_and_filter_bs_list(
        siret: str,
        dfs_to_process: list[tuple[str, pl.LazyFrame]],
        processing_codes: list[str],
        data_date_interval: tuple[datetime, datetime],
        packagings_data_df: pl.LazyFrame | None,
    ) -> pl.LazyFrame:
        bs_dfs = []
        for bs_type, df in dfs_to_process:
            if df is None:
                continue

            df_filtered = pl.LazyFrame()
            if bs_type != BSFF:
                df_filtered = df.filter(
                    (pl.col("recipient_company_siret") == siret)
                    & (pl.col("processing_operation_code").is_in(processing_codes))
                    & (pl.col("processed_at").is_between(*data_date_interval))
                )
            else:
                if packagings_data_df is not None:
                    df = df.join(
                        packagings_data_df.select(
                            [
                                "bsff_id",
                                "acceptation_weight",
                                "operation_date",
                                "operation_code",
                            ]
                        ),
                        left_on="id",
                        right_on="bsff_id",
                        validate="1:m",
                    )
                    df = df.filter(
                        (pl.col("recipient_company_siret") == siret)
                        & (pl.col("operation_code").is_in(processing_codes))
                        & (pl.col("operation_date").is_between(*data_date_interval))
                    )
                    df_filtered = df.group_by("id").agg(
                        pl.col("operation_code").max().alias("processing_operation_code"),
                        pl.col("operation_date").max().alias("processed_at"),
                        pl.col("acceptation_weight").sum().alias("quantity_received"),
                    )
                else:
                    continue

            df_filtered = df_filtered.with_columns(pl.lit(bs_type.upper()).alias("bs_type"))
            bs_dfs.append(df_filtered)

        concat_df = pl.LazyFrame()
        if len(bs_dfs) > 0:
            concat_df = pl.concat(bs_dfs, how="diagonal").sort(["bs_type", "processed_at"])

        return concat_df

    def _preprocess_data(self) -> None:
        self._preprocess_data_multi_rubriques()
        self._preprocess_data_single_rubrique()
        self._preprocess_non_dangerous_rubriques()

    def _check_data_empty(self) -> bool:
        if all(len(e) == 0 for e in self.preprocessed_data.values()):
            return True

        return False

    def _add_stats(self) -> dict[str, list]:
        stats = {"dangerous": [], "non_dangerous": []}

        for item in self.preprocessed_data["dangerous"]:
            if not item:
                continue
            df: pl.LazyFrame = item["bs_list"]
            if df is not None:
                rows = []

                if "quantity_refused" in df.columns:
                    df = df.with_columns(
                        (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                            "quantity_received"
                        )
                    )

                for e in df.iter_rows(named=True):
                    row = {
                        "id": e["readable_id"] if e["bs_type"] == "BSDD" else e["id"],
                        "bs_type": e["bs_type"],
                        "waste_code": e["waste_code"],
                        "waste_name": e["waste_name"] if (e["bs_type"] not in ("BSVHU", "BSDASRI")) else None,
                        "operation_code": e["processing_operation_code"],
                        "quantity": format_number_str(e["quantity_received"], 3)
                        if e["quantity_received"] is not None
                        else None,
                        "processed_at": e["processed_at"].strftime("%d/%m/%Y %H:%M")
                        if e["processed_at"] is not None
                        else None,
                    }
                    rows.append(row)
                stats["dangerous"].append({**item, "bs_list": rows})

        for item in self.preprocessed_data["non_dangerous"]:
            df: pl.DataFrame = item["statements_list"]
            rows = []
            for e in df.iter_rows(named=True):
                row = {
                    "waste_code": e["waste_code"],
                    "waste_name": e["waste_description"],
                    "operation_code": e["operation_code"],
                    "quantity": format_number_str(e["weight_value"], 3) if e["weight_value"] is not None else None,
                    "received_at": e["reception_date"].strftime("%d/%m/%Y")
                    if e["reception_date"] is not None
                    else None,
                }
                rows.append(row)
            stats["non_dangerous"].append({**item, "statements_list": rows})
        return stats

    def build(self) -> dict:
        self._preprocess_data()

        if not self._check_data_empty():
            return self._add_stats()
        return {}


class LinkedCompaniesProcessor:
    """Component that displays list of ICPE authorized items.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    linked_companies_data: LazyFrame
        LazyFrame containing list of linked companies
    """

    def __init__(
        self,
        company_siret: str,
        linked_companies_data: pl.LazyFrame | None,
    ) -> None:
        self.company_siret = company_siret
        self.linked_companies_data = linked_companies_data.collect()

        self.preprocessed_df = None

    def _preprocess_data(self):
        df = self.linked_companies_data
        if df is None:
            return

        df = df.filter(pl.col("siret") != self.company_siret)
        if len(df) == 0:
            return

        df = df.sort("created_at")

        self.preprocessed_df = df

    def build_context(self):
        data = self.preprocessed_df

        data = data.with_columns(pl.col("created_at").dt.strftime("%d/%m/%Y"))

        json_data = {
            "siren": self.company_siret[:9],
            "siret_list": data.to_dicts(),
        }
        return json_data

    def _check_empty_data(self) -> bool:
        if self.preprocessed_df is None or len(self.preprocessed_df) == 0:
            return True

        return False

    def build(self):
        self._preprocess_data()

        data = {}
        if not self._check_empty_data():
            data = self.build_context()

        return data


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


class TransporterBordereauxStatsProcessor:
    """Component that compute statistics about number of bordereaux as transporter company and corresponding quantities.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    transporters_data_df: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau transported data.
        Correspond to the new way of managing transporters in Trackdéchets.
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    data_date_interval: tuple
        Date interval to filter data.
    packagings_data_df : pl.LazyFrame | None
        Optional parameter that represents a LazyFrame containing data about BSFF packagings.
    """

    def __init__(
        self,
        company_siret: str,
        transporters_data_df: Dict[str, pl.LazyFrame],  # Handling new multi-modal Trackdéchets feature
        bs_data_dfs: Dict[str, pl.LazyFrame],
        data_date_interval: tuple[datetime, datetime],
        packagings_data_df: pl.LazyFrame | None = None,
    ) -> None:
        self.company_siret = company_siret
        self.transporters_data_df = transporters_data_df
        self.bs_data_dfs = bs_data_dfs
        self.data_date_interval = data_date_interval
        self.packagings_data_df = packagings_data_df

        self.transported_bordereaux_stats = {
            BSDD: {},
            BSDD_NON_DANGEROUS: {},
            BSDA: {},
            BSFF: {},
            BSDASRI: {},
            BSVHU: {},
        }

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it to be displayed."""
        transporter_data_dfs = self.transporters_data_df
        bs_data_dfs = self.bs_data_dfs

        for bs_type, df in chain(transporter_data_dfs.items(), bs_data_dfs.items()):
            df = df.filter(
                pl.col("sent_at").is_between(*self.data_date_interval)
                & (pl.col("transporter_company_siret") == self.company_siret)
            )

            id_col = "bs_id" if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDA, BSFF] else "id"

            num_bordereaux = df.select(pl.col(id_col).n_unique()).collect().item()
            quantity = df.select(pl.col("quantity_received").sum()).collect().item()
            self.transported_bordereaux_stats[bs_type]["count"] = num_bordereaux
            self.transported_bordereaux_stats[bs_type]["quantity"] = format_number_str(quantity, 2)

    def _check_data_empty(self) -> bool:
        if all((e is None) or (e == {}) for e in self.transported_bordereaux_stats.values()):
            return True

        return False

    def build(self):
        self._preprocess_bs_data()

        data = {}
        if not self._check_data_empty():
            data = self.transported_bordereaux_stats

        return data


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


class GistridStatsProcessor:
    """Component that compute statistics about Gistrid/PNTTD data.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    gistrid_data_df: pl.LazyFrame
        LazyFrame containing Gistrid notifications.
    """

    def __init__(self, company_siret: str, gistrid_data_df: pl.LazyFrame | None) -> None:
        self.company_siret = company_siret
        self.gistrid_data_df = gistrid_data_df

        self.gistrid_stats = {}

    def _preprocess_gistrid_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it to be displayed."""
        df = self.gistrid_data_df
        if df is None:
            return

        df = self.gistrid_data_df

        df = df.with_columns(
            pl.col("date_autorisee_fin_transferts").str.slice(-2, None).alias("annee_fin_autorisation")
        )

        import_data = df.filter(pl.col("siret_installation_traitement") == self.company_siret)

        import_data_grouped = (
            import_data.group_by(["annee_fin_autorisation", "numero_gistrid_notifiant"])
            .agg(
                pl.col("nom_notifiant").max().alias("nom_origine"),
                pl.col("pays_notifiant").max().alias("pays_origine"),
                pl.col("somme_quantites_recues").sum().alias("quantites_recues"),
                pl.col("nombre_transferts_receptionnes").sum().alias("nombre_transferts"),
                pl.col("code_ced")
                .str.join(", ")
                .str.split(", ")
                .list.unique()
                .str.join(", ")
                .alias("codes_dechets"),  # To avoid duplicates in list
                pl.col("code_d_r")
                .str.join(", ")
                .str.split(", ")
                .list.unique()
                .str.join(", ")
                .alias("codes_operations"),  # To avoid duplicates in list
            )
            .sort("annee_fin_autorisation")
            .with_columns(
                pl.col("quantites_recues").map_elements(lambda x: format_number_str(x, 2), return_dtype=pl.String)
            )
            .collect()
        )
        if len(import_data_grouped) > 0:
            self.gistrid_stats["import"] = import_data_grouped.to_dicts()
            self.gistrid_stats["numero_gistrid"] = (
                import_data.select(pl.col("numero_gistrid_installation_traitement").first()).collect().item()
            )

        export_data = df.filter(pl.col("siret_notifiant") == self.company_siret)

        export_data_grouped = (
            export_data.group_by(
                ["annee_fin_autorisation", "numero_gistrid_installation_traitement"],
            )
            .agg(
                pl.col("nom_installation_traitement").max().alias("nom_destination"),
                pl.col("pays_installation_traitement").max().alias("pays_destination"),
                pl.col("somme_quantites_recues").sum().alias("quantites_recues"),
                pl.col("nombre_transferts_receptionnes").sum().alias("nombre_transferts"),
                pl.col("code_ced")
                .str.join(", ")
                .str.split(", ")
                .list.unique()
                .str.join(", ")
                .alias("codes_dechets"),  # To avoid duplicates in list
                pl.col("code_d_r")
                .str.join(", ")
                .str.split(", ")
                .list.unique()
                .str.join(", ")
                .alias("codes_operations"),  # To avoid duplicates in list
            )
            .sort("annee_fin_autorisation")
            .with_columns(
                pl.col("quantites_recues").map_elements(lambda x: format_number_str(x, 2), return_dtype=pl.String)
            )
            .collect()
        )
        if len(export_data_grouped) > 0:
            self.gistrid_stats["export"] = export_data_grouped.to_dicts()
            self.gistrid_stats["numero_gistrid"] = (
                export_data.select(pl.col("numero_gistrid_notifiant").first()).collect().item()
            )

    def _check_data_empty(self) -> bool:
        if len(self.gistrid_stats) == 0:
            return True

        return False

    def build(self):
        self._preprocess_gistrid_data()

        data = {}
        if not self._check_data_empty():
            data = self.gistrid_stats

        return data


class RegistryStatsProcessor:
    """Component that displays aggregated data about registries non dangerous waste data.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    registry_incoming_data: LazyFrame
        LazyFrame containing data for incoming non dangerous waste (from registry).
    registry_outgoing_data: LazyFrame
        LazyFrame containing data for outgoing non dangerous waste (from registry).
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        registry_incoming_data: pl.LazyFrame,
        registry_outgoing_data: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.registry_incoming_data = registry_incoming_data
        self.registry_outgoing_data = registry_outgoing_data
        self.data_date_interval = data_date_interval

        # Init all statistics
        self.stats = {
            "total_weight_incoming": 0,
            "total_weight_outgoing": 0,
            "bar_size_weight_incoming": None,
            "bar_size_weight_outgoing": None,
            "has_weight": None,
            "total_volume_incoming": 0,
            "total_volume_outgoing": 0,
            "bar_size_volume_incoming": None,
            "bar_size_volume_outgoing": None,
            "has_volume": None,
            "total_statements_incoming": 0,
            "total_statements_outgoing": 0,
        }

    def _check_data_empty(self) -> bool:
        # If all values after preprocessing are empty, then output data will be empty
        if all((e == 0) or (e is None) for e in self.stats.values()):
            return True

        return False

    def _preprocess_data(self) -> None:
        incoming_data = self.registry_incoming_data
        outgoing_data = self.registry_outgoing_data

        for data_suffix, data_to_process, date_col in [
            ("incoming", incoming_data, "reception_date"),
            ("outgoing", outgoing_data, "dispatch_date"),
        ]:
            if data_to_process is not None:
                data = data_to_process.filter(
                    pl.col(date_col).is_between(*self.data_date_interval) & (pl.col("siret") == self.company_siret)
                )

                self.stats[f"total_statements_{data_suffix}"] = data.select(pl.col("id").n_unique()).collect().item()
                for quantity_col, key in [("weight_value", "weight"), ("volume", "volume")]:
                    total = data.select(pl.col(quantity_col).sum()).collect().item()
                    if total is not None:
                        self.stats[f"total_{key}_{data_suffix}"] = total

        for key in ["weight", "volume"]:
            incoming_bar_size = 0
            outgoing_bar_size = 0

            total_quantity_incoming = self.stats[f"total_{key}_incoming"]
            total_quantity_outgoing = self.stats[f"total_{key}_outgoing"]
            if not (total_quantity_incoming == total_quantity_outgoing == 0):
                # The bar sizes are relative to the largest quantity.
                # Size is expressed as percentage of the component width.
                if total_quantity_incoming > total_quantity_outgoing:
                    incoming_bar_size = 100
                    outgoing_bar_size = int(100 * (total_quantity_outgoing / total_quantity_incoming))
                else:
                    incoming_bar_size = int(100 * (total_quantity_incoming / total_quantity_outgoing))
                    outgoing_bar_size = 100
                self.stats[f"has_{key}"] = True
            else:
                self.stats[f"has_{key}"] = False
            self.stats[f"bar_size_{key}_incoming"] = incoming_bar_size
            self.stats[f"bar_size_{key}_outgoing"] = outgoing_bar_size

    def build_context(self):
        # We use the format_number_str only on variables that holds
        # quantity values.

        precisions = {
            "total_weight_incoming": 2,
            "total_weight_outgoing": 2,
            "bar_size_weight_incoming": 2,
            "bar_size_weight_outgoing": 2,
            "total_volume_incoming": 2,
            "total_volume_outgoing": 2,
            "bar_size_volume_incoming": 2,
            "bar_size_volume_outgoing": 2,
            "total_statements_incoming": 0,
            "total_statements_outgoing": 0,
        }

        ctx = {
            k: format_number_str(v, precisions[k])
            if (isinstance(v, numbers.Number) and not isinstance(v, bool))
            else v
            for k, v in self.stats.items()
        }

        return ctx

    def build(self):
        self._preprocess_data()

        data = {}
        if not self._check_data_empty():
            data = self.build_context()
        return data


class IntermediaryBordereauxStatsProcessor:
    """Component that compute statistics about number of bordereaux as "eco-organisme" and corresponding quantities.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    transporters_data_df: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau transported data.
        Correspond to the new way of managing transporters in Trackdéchets.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        transporters_data_df: Dict[str, pl.LazyFrame],  # Handling new multi-modal Trackdéchets feature
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.bs_data_dfs = bs_data_dfs
        self.transporters_data_df = transporters_data_df
        self.data_date_interval = data_date_interval

        self.bordereaux_stats = {
            BSDD: {},
            BSDD_NON_DANGEROUS: {},
            BSDA: {},
            BSDASRI: {},
        }

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it to be displayed."""
        bs_data_dfs = self.bs_data_dfs

        for bs_type, df in bs_data_dfs.items():
            if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDA]:
                transport_df = self.transporters_data_df.get(bs_type)

                if transport_df is None:
                    continue

                df = df.select(pl.selectors.exclude("sent_at"))  # To avoid column duplication with transport data

                df = df.join(
                    transport_df.select(["bs_id", "sent_at"]),
                    left_on="id",
                    right_on="bs_id",
                    how="left",
                    validate="1:m",
                )

            df = df.filter(
                pl.col("sent_at").is_between(*self.data_date_interval)
                & (pl.col("eco_organisme_siret") == self.company_siret)
            )
            df = df.unique("id")

            num_bordereaux = df.select(pl.col("id").n_unique()).collect().item()

            # handle quantity refused
            if bs_type in [BSDD, BSDD_NON_DANGEROUS]:
                df = df.with_columns(
                    (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                        "quantity_received"
                    )
                )

            quantity = df.unique("id").select(pl.col("quantity_received").sum()).collect().item()
            self.bordereaux_stats[bs_type]["count"] = format_number_str(num_bordereaux, 0)
            self.bordereaux_stats[bs_type]["quantity"] = format_number_str(quantity, 2)

    def _check_data_empty(self) -> bool:
        if all((e is None) or (e == {}) for e in self.bordereaux_stats.values()):
            return True

        return False

    def build(self):
        self._preprocess_bs_data()

        data = {}
        if not self._check_data_empty():
            data = self.bordereaux_stats

        return data


class IncineratorOutgoingWasteProcessor:
    """Component that aggregate data to show a table of outgoing dangerous and non dangerous waste for incinerators.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    bs_data_dfs: dict
        Dict with key being the 'bordereau' type and values the LazyFrame containing the bordereau data.
    icpe_data: LazyFrame
        LazyFrame containing list of ICPE authorized items
    registry_outgoing_data: LazyFrame
        LazyFrame containing data for outgoing non dangerous waste (from registry).
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        transporters_data_df: Dict[str, pl.LazyFrame],  # Handling new multi-modal Trackdéchets feature
        icpe_data: pl.LazyFrame | None,
        registry_outgoing_data: pl.LazyFrame | None,
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.bs_data_dfs = bs_data_dfs
        self.transporters_data_df = transporters_data_df
        self.icpe_data = icpe_data
        self.registry_outgoing_data = registry_outgoing_data
        self.data_date_interval = data_date_interval

        self.preprocessed_data = {"dangerous": pl.DataFrame(), "non_dangerous": pl.DataFrame()}

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it to be displayed."""
        bs_data_dfs = self.bs_data_dfs

        dfs_to_concat = []
        for bs_type, df in bs_data_dfs.items():
            if bs_type in [BSDD, BSDD_NON_DANGEROUS, BSDA]:
                transport_df = self.transporters_data_df.get(bs_type)

                if transport_df is None:
                    continue

                df = df.select(pl.selectors.exclude("sent_at"))  # To avoid column duplication with transport data

                df = df.join(
                    transport_df.select(["bs_id", "sent_at"]),
                    left_on="id",
                    right_on="bs_id",
                    how="left",
                    validate="1:m",
                )

            df = df.filter(
                pl.col("sent_at").is_between(*self.data_date_interval)
                & (pl.col("emitter_company_siret") == self.company_siret)
            )
            df = df.unique("id")
            dfs_to_concat.append(df)

        if len(dfs_to_concat) > 0:
            concat_df: pl.LazyFrame = pl.concat(dfs_to_concat, how="diagonal")

            concat_df = concat_df.with_columns(pl.col("waste_name").fill_null(""))
            # Handle quantity refused
            if "quantity_refused" in concat_df.columns:
                concat_df = concat_df.with_columns(
                    (pl.col("quantity_received") - pl.col("quantity_refused").fill_nan(0).fill_null(0)).alias(
                        "quantity_received"
                    )
                )

            aggregated_data_df = (
                concat_df.group_by(["waste_code", "recipient_company_siret", "processing_operation_code"])
                .agg(
                    pl.col("quantity_received").sum().alias("quantity"), pl.col("waste_name").max().alias("waste_name")
                )
                .sort(["waste_code", "recipient_company_siret", "quantity"], descending=[False, False, True])
            ).collect()

            if len(aggregated_data_df) > 0:
                self.preprocessed_data["dangerous"] = aggregated_data_df

    def _preprocess_registry_statements_data(self) -> None:
        """Preprocess raw registry statements data to prepare it to be displayed."""
        registry_data = self.registry_outgoing_data

        if registry_data is None:
            return

        registry_data = registry_data.with_columns(pl.col("waste_description").fill_null(""))

        dfs = []
        for quantity_colname in ["weight_value", "volume"]:
            aggregated_data_df = (
                registry_data.filter(
                    (pl.col("siret") == self.company_siret)
                    & (pl.col("dispatch_date").is_between(*self.data_date_interval))
                )
                .group_by(["waste_code", "destination_company_org_id", "operation_code"])
                .agg(
                    pl.col(quantity_colname).sum().alias("quantity"),
                    pl.col("waste_description").max().alias("waste_name"),
                )
                .sort(["waste_code", "destination_company_org_id", "quantity"], descending=[False, False, True])
                .with_columns(pl.lit("t" if quantity_colname == "weight_value" else "m³").alias("unit"))
                .filter(pl.col("quantity") > 0)
            ).collect()

            if len(aggregated_data_df):
                dfs.append(aggregated_data_df)

        if len(dfs) > 0:
            final_df = pl.concat(dfs, how="diagonal")
            self.preprocessed_data["non_dangerous"] = final_df

    def is_incinerator(self, dangerous_waste: bool) -> bool:
        rubrique = "2770" if dangerous_waste else "2771"

        icpe_data = self.icpe_data
        if icpe_data is None:
            return False
        icpe_data = icpe_data.collect()
        if len(icpe_data) == 0:
            return False

        return icpe_data.select((pl.col("rubrique") == rubrique).any()).item()

    def _preprocess_data(self):
        if self.is_incinerator(dangerous_waste=True):
            self._preprocess_bs_data()
        if self.is_incinerator(dangerous_waste=False):
            self._preprocess_registry_statements_data()

    def _check_data_empty(self) -> bool:
        if all((e is None) or (len(e) == 0) for e in self.preprocessed_data.values()):
            return True

        return False

    def _serialize_stats(self) -> dict:
        res = {"dangerous": [], "non_dangerous": []}

        for row in self.preprocessed_data["dangerous"].iter_rows(named=True):
            res["dangerous"].append(
                {
                    "waste_code": row["waste_code"],
                    "waste_name": row["waste_name"],
                    "destination_company_siret": row["recipient_company_siret"],
                    "processing_opration": row["processing_operation_code"],
                    "quantity": format_number_str(row["quantity"], 2),
                }
            )

        for row in self.preprocessed_data["non_dangerous"].iter_rows(named=True):
            res["non_dangerous"].append(
                {
                    "waste_code": row["waste_code"],
                    "waste_name": row["waste_name"],
                    "destination_company_siret": row["destination_company_org_id"],
                    "unit": row["unit"],
                    "processing_opration": row["operation_code"],
                    "quantity": format_number_str(row["quantity"], 2),
                }
            )
        return res

    def build(self):
        self._preprocess_data()

        data = {}
        if not self._check_data_empty():
            data = self._serialize_stats()

        return data


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


class RegistryTransporterStatsProcessor:
    """Component that compute statistics about number of RDNTS statements as transporter company and corresponding quantities.

    Parameters
    ----------
    company_siret: str
        SIRET number of the establishment for which the data is displayed (used for data preprocessing).
    registry_data: dict
        Dict with key being the registry type and values the LazyFrame containing the statements data.
    data_date_interval: tuple
        Date interval to filter data.
    """

    def __init__(
        self,
        company_siret: str,
        registry_data: Dict[str, pl.LazyFrame | None],
        data_date_interval: tuple[datetime, datetime],
    ) -> None:
        self.company_siret = company_siret
        self.registry_data = registry_data
        self.data_date_interval = data_date_interval

        self.transported_statements_stats = {
            "ndw_incoming": {},
            "ndw_outgoing": {},
            "excavated_land_incoming": {},
            "excavated_land_outgoing": {},
        }

    def _preprocess_bs_data(self) -> None:
        """Preprocess raw 'bordereaux' data to prepare it to be displayed."""

        registry_data = self.registry_data

        for key, date_col in [
            ("ndw_incoming", "reception_date"),
            ("ndw_outgoing", "dispatch_date"),
            ("excavated_land_incoming", "reception_date"),
            ("excavated_land_outgoing", "dispatch_date"),
        ]:
            df = registry_data[key]
            if df is None:
                continue

            df = (
                df.filter(
                    pl.col(date_col).is_between(*self.data_date_interval)
                    & (pl.col("transporters_org_ids").list.contains(self.company_siret))
                )
                .select(
                    pl.col("id").n_unique().alias("num_statements"),
                    pl.col("weight_value").sum().alias("mass_quantity"),
                    pl.col("volume").sum().alias("volume_quantity"),
                )
                .collect()
            )

            if len(df) > 0:
                num_statements = df["num_statements"].item()
                mass_quantity = df["mass_quantity"].item()
                volume_quantity = df["volume_quantity"].item()

                if num_statements is not None:
                    self.transported_statements_stats[key]["count"] = num_statements
                if mass_quantity is not None:
                    self.transported_statements_stats[key]["mass_quantity"] = format_number_str(mass_quantity, 2)
                if volume_quantity is not None:
                    self.transported_statements_stats[key]["volume_quantity"] = format_number_str(volume_quantity, 2)

    def _check_data_empty(self) -> bool:
        if all(
            (e is None) or (e == {}) or (all(y == 0 for y in e.values()))
            for e in self.transported_statements_stats.values()
        ):
            return True

        return False

    def build(self):
        self._preprocess_bs_data()

        data = {}
        if not self._check_data_empty():
            data = self.transported_statements_stats

        return data
