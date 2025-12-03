import numbers
from datetime import datetime

import polars as pl

from sheets.utils import format_number_str


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
