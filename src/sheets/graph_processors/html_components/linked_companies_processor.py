import polars as pl


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
