from django.core.management.base import BaseCommand

from ...models import NafCode
from ...naf_codes import NAF_CODES


class Command(BaseCommand):
    def handle(self, verbosity=0, **options):
        NafCode.objects.all().delete()
        for code in NAF_CODES:
            NafCode.objects.create(code=code["id"], content=code["label"])
