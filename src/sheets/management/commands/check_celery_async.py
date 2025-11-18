from django.core.management.base import BaseCommand

from sheets.task import create_dummy_file


class Command(BaseCommand):
    def handle(self, verbosity=0, **kwargs):
        task = create_dummy_file.delay()
        self.stdout.write(f"Task created {task}")
