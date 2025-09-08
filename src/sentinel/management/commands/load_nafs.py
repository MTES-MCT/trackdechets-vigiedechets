from django.core.management.base import BaseCommand

from ...models import NafCode
from ...naf_codes import NAF_CODES


class Command(BaseCommand):
    """Create a tree of naf codes"""

    def add_arguments(self, parser):
        parser.add_argument("--force-load", action="store_true", help="Force load data even if it already exists")

    def handle(self, verbosity=0, **options):
        force_load = options["force_load"]
        if NafCode.objects.exists() and not force_load:
            print("exit")
            return

        # 2 pass, create then set parent
        NafCode.objects.all().delete()

        # first pass: create all objects without parents
        created_codes = {}
        for code_data in NAF_CODES:
            naf_code = NafCode.objects.create(code=code_data["id"], content=code_data["label"])
            created_codes[code_data["id"]] = naf_code

        # Second pass: set parent relationships
        for code_data in NAF_CODES:
            code = code_data["id"]
            naf_code = created_codes[code]

            # Find parent code
            parent_code = self.get_parent_code(code)
            if parent_code and parent_code in created_codes:
                naf_code.parent = created_codes[parent_code]
                naf_code.save()

    def get_parent_code(self, code):
        """
        Get the parent code based on hierarchical structure.
        Examples:
        - "01.11Z" -> "01.11"
        - "01.11" -> "01.1"
        - "01.1" -> "01"
        - "01" -> None (top level)
        """
        # If code ends with a letter, removes it to get parent
        if code[-1].isalpha():
            return code[:-1]

        # If code contains dots, removes the last part
        if "." in code:
            parts = code.split(".")
            if len(parts) > 1:
                return ".".join(parts[:-1])

        # Top level code, no parent
        return None
