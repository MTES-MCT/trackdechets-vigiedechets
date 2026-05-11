from django.core.management.base import BaseCommand

from maps.processors.stats_processor import build_stats_and_figs

from ...processors.clear import clear_figs
from ...processors.create_df import build_dataframes


class Command(BaseCommand):
    help = "Build stats and figures for all years"

    def handle(self, verbosity=0, **options):
        self.stdout.write("Clearing existing figs...")
        clear_figs()

        self.stdout.write("Building dataframes...")
        build_dataframes()

        for year in [2022, 2023, 2024, 2025, 2026]:
            self.stdout.write(f"Building stats and figs for year {year}...")
            build_stats_and_figs(year, clear_year=True)
            self.stdout.write(self.style.SUCCESS(f"Stats and figs built for year {year}"))
