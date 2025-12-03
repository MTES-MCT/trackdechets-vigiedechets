import polars as pl

from sheets.utils import format_number_str


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
