from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    """Call several cleanup commands to limit cron tasks"""

    def handle(self, verbosity=0, **options):
        call_command("cleanup_django_defender")
        call_command("clearsessions")
        call_command("void_sheets")
