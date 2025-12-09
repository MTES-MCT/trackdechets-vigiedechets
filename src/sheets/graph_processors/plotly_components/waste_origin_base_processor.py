from datetime import datetime
from typing import Dict

import polars as pl


class WasteOriginBaseProcessor:
    """Base processor for waste origin visualizations.

    This abstract class provides shared pre-processing and BSFF-specific
    data handling logic for waste origin chart and map components.

    Parameters
    ----------
    company_siret : str
        SIRET number for the establishment whose data is visualized.
    bs_data_dfs : dict
        Dictionary mapping 'bordereau' types to polars LazyFrame objects containing
        traceability/waste receipt data.
    departements_regions_df : LazyFrame
        Static dataset linking département codes to labels and associated regions.
    data_date_interval : tuple
        Tuple of (start_datetime, end_datetime) for filtering input datasets.
    packagings_data : LazyFrame, optional
        Dataset of packaging-level BSFF data, required for accurate
        received-quantity calculations with BSFF traceability data.
    """

    def __init__(
        self,
        company_siret: str,
        bs_data_dfs: Dict[str, pl.LazyFrame],
        departements_regions_df: pl.LazyFrame,
        data_date_interval: tuple[datetime, datetime],
        packagings_data: pl.LazyFrame | None = None,
    ) -> None:
        self.company_siret = company_siret
        self.bs_data_dfs = bs_data_dfs
        self.departements_regions_df = departements_regions_df
        self.data_date_interval = data_date_interval
        self.packagings_data = packagings_data

        self.figure = None

    @staticmethod
    def _process_bsff_data(
        packagings_data: pl.LazyFrame | None, bsff_df: pl.LazyFrame | None = None
    ) -> pl.LazyFrame | None:
        """Processes BSFF data to compute waste quantities received per container.

        This method joins BSFF bordereau data with packagings data to obtain precise accepted quantities at the container level.
        It then aggregates these container quantities to the bordereau level for each waste receipt.

        Returns
        -------
        LazyFrame | None
            - If both `bsff_df` and `packagings_data` are provided, returns a LazyFrame of processed BSFF data,
              grouped by bordereau ID with sum of received quantities and other relevant fields.
            - If either `bsff_df` or `packagings_data` is missing, returns None.
        """

        if bsff_df is None:
            return
        elif packagings_data is None:
            return
        else:
            # Join packagings data to get quantities
            df = bsff_df.join(
                packagings_data.select(["bsff_id", "acceptation_weight", "acceptation_date"]),
                left_on="id",
                right_on="bsff_id",
                validate="1:m",
            )
            # Use acceptation_date for received_at when filtering incoming data
            df = df.with_columns(pl.coalesce(pl.col("acceptation_date"), pl.col("received_at")).alias("received_at"))
            df = df.rename({"acceptation_weight": "quantity_received"})

            # Re-aggregate at bordereau level
            df = df.group_by("id").agg(
                pl.col("emitter_company_siret").max(),
                pl.col("emitter_company_address").max(),
                pl.col("recipient_company_siret").max(),
                pl.col("quantity_received").sum(),  # Sum of container quantities
                pl.col("received_at").min(),
            )
            return df

    def _preprocess_data(self) -> None:
        raise NotImplementedError("This method is not implemented for the base processor.")

    def _create_figure(self) -> None:
        raise NotImplementedError("This method is not implemented for the base processor.")

    def _check_data_empty(self) -> bool:
        raise NotImplementedError("This method is not implemented for the base processor.")

    def build(self):
        self._preprocess_data()

        figure = {}
        if not self._check_data_empty():
            self._create_figure()
            figure = self.figure.to_json()

        return figure
