import datetime

from django.core.management.base import BaseCommand

from sheets.data_processing import SheetProcessor
from sheets.models import ComputedInspectionData


class Command(BaseCommand):
    help = "Create and process an inspection sheet for a given SIRET and date range."

    def add_arguments(self, parser):
        parser.add_argument("siret", help="SIRET number of the company")
        parser.add_argument(
            "--start",
            default="2024-01-01",
            help="Start date in YYYY-MM-DD format (default: 2024-01-01)",
        )
        parser.add_argument(
            "--end",
            default=datetime.date.today().strftime("%Y-%m-%d"),
            help="End date in YYYY-MM-DD format (default: today)",
        )

    def handle(self, **options):
        siret = options["siret"]
        start = datetime.datetime.strptime(options["start"], "%Y-%m-%d")
        end = datetime.datetime.strptime(options["end"], "%Y-%m-%d")

        sheet = ComputedInspectionData.objects.create(
            org_id=siret,
            data_start_date=start,
            data_end_date=end,
            created_by="cli",
        )
        self.stdout.write(f"Created sheet {sheet.pk} for {siret} ({start.date()} → {end.date()})")

        SheetProcessor(sheet.pk).process()

        sheet.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(f"Done — state: {sheet.state} | URL: /sheets/{sheet.pk}"))
