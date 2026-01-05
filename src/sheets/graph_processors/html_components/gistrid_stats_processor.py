import polars as pl

from sheets.utils import format_number_str


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
                .list.join(", ")
                .alias("codes_dechets"),  # To avoid duplicates in list
                pl.col("code_d_r")
                .str.join(", ")
                .str.split(", ")
                .list.unique()
                .list.join(", ")
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
                .list.join(", ")
                .alias("codes_dechets"),  # To avoid duplicates in list
                pl.col("code_d_r")
                .str.join(", ")
                .str.split(", ")
                .list.unique()
                .list.join(", ")
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
