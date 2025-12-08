from datetime import datetime
from typing import Dict

import polars as pl

from sheets.utils import format_number_str

from ...constants import BSDA, BSDASRI, BSDD, BSDD_NON_DANGEROUS, BSFF, BSVHU


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
                    return  # TODO: Probably should continue instead of returning here

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

        has_quantity_refused = "quantity_refused" in self.preprocessed_data.collect_schema().names()

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
