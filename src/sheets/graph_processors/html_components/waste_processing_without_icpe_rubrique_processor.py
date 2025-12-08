from datetime import datetime
from typing import Dict

import polars as pl

from sheets.utils import format_number_str

from ...constants import BSDA, BSDASRI, BSDD, BSFF, BSVHU


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
                if "quantity_refused" in bs_df.collect_schema().names():
                    filter_expr = (
                        pl.col("quantity_received") - pl.col("quantity_refused").fill_null(0).fill_nan(0)
                    ) > 0

                bs_df = bs_df.filter(filter_expr)

                bs_df = bs_df.collect()  # Creates the list of bordereaux

                if len(bs_df) > 0:
                    total_quantity = bs_df.select(pl.col("quantity_received").sum()).item()
                    if "quantity_refused" in bs_df.collect_schema().names():
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

                if "quantity_refused" in bs_filtered_df.collect_schema().names():
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

                if "quantity_refused" in df.collect_schema().names():
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
