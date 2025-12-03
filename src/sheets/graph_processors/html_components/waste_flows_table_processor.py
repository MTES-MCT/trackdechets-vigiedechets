from datetime import datetime
from typing import Dict

import polars as pl

from sheets.utils import format_number_str

from ...constants import BS_TYPES_WITH_MULTIMODAL_TRANSPORT, BSDD, BSDD_NON_DANGEROUS, BSFF


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
            cols_used = [
                "id",
                "emitter_company_siret",
                "recipient_company_siret",
                "transporter_company_siret",
                "sent_at",
                "received_at",
                "waste_code",
                "quantity_received",
                "quantity_refused",
            ]
            cols_present = [col for col in cols_used if col in df.collect_schema().names()]
            if cols_present:
                df = df.select(cols_present)
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
            if (siret_key in df.collect_schema().names()) and (date_key in df.collect_schema().names()):
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
