from datetime import datetime
from typing import Dict

import polars as pl

from sheets.utils import format_number_str

from ...constants import BSDA, BSDD, BSDD_NON_DANGEROUS


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
            if "quantity_refused" in concat_df.collect_schema().names():
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
