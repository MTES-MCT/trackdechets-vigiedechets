import sys

from celery import current_app
from celery.utils.time import humanize_seconds
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check Celery configuration and worker status"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Display detailed information",
        )

    def handle(self, *args, **options):
        verbose = options.get("verbose", False)

        self.stdout.write(self.style.HTTP_INFO("Checking Celery configuration..."))
        self.stdout.write("")

        # Check broker connection
        try:
            inspect = current_app.control.inspect()

            # Get active workers
            stats = inspect.stats()

            if not stats:
                self.stdout.write(self.style.WARNING("⚠ No active Celery workers found"))
                self.stdout.write(
                    self.style.WARNING("Make sure workers are running with: celery -A your_project worker -l info")
                )
                sys.exit(1)

            self.stdout.write(self.style.SUCCESS(f"✓ Found {len(stats)} active worker(s)"))

            # Display worker information
            for worker_name, worker_stats in stats.items():
                self.stdout.write(f"\n  Worker: {self.style.HTTP_INFO(worker_name)}")

                if verbose:
                    self.stdout.write(f"    Pool: {worker_stats.get('pool', {}).get('implementation')}")
                    self.stdout.write(f"    Max concurrency: {worker_stats.get('pool', {}).get('max-concurrency')}")

                    uptime = worker_stats.get("clock", {})
                    if uptime:
                        self.stdout.write(f"    Uptime: {humanize_seconds(int(uptime))}")

            # Check active tasks
            active = inspect.active()
            if active:
                total_active = sum(len(tasks) for tasks in active.values())
                self.stdout.write(f"\n✓ {total_active} active task(s)")
            else:
                self.stdout.write("\n✓ No active tasks")

            # Check scheduled tasks
            scheduled = inspect.scheduled()
            if scheduled:
                total_scheduled = sum(len(tasks) for tasks in scheduled.values())
                self.stdout.write(f"✓ {total_scheduled} scheduled task(s)")

            # Check registered tasks
            registered = inspect.registered()
            if registered and verbose:
                self.stdout.write("\n  Registered tasks:")
                for worker, tasks in registered.items():
                    for task in sorted(tasks):
                        if not task.startswith("celery."):
                            self.stdout.write(f"    - {task}")

            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("✓ Celery is configured correctly and workers are running"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error connecting to Celery: {str(e)}"))
            self.stdout.write(self.style.ERROR("\nPossible issues:"))
            self.stdout.write("  - Celery workers are not running")
            self.stdout.write("  - Broker (Redis/RabbitMQ) is not accessible")
            self.stdout.write("  - Incorrect CELERY_BROKER_URL configuration")
            sys.exit(1)
