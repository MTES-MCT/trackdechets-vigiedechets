import datetime as dt

import pandas as pd
from django.core.management.base import BaseCommand

from sheets.data_extraction import build_query

from ...models import CartoCompany

BASE_QUERY = """
SELECT
    ce.siret,
    ce.nom_etablissement,
    ce.profils,
    ce.profils_collecteur,
    ce.profils_installation,
    ce.profils_installation_vhu,
    ce.bsdd,
    ce.bsdd_emitter,
    ce.bsdd_transporter,
    ce.bsdd_destination,
    ce.bsdnd,
    ce.bsdnd_emitter,
    ce.bsdnd_transporter,
    ce.bsdnd_destination,
    ce.bsda,
    ce.bsda_emitter,
    ce.bsda_transporter,
    ce.bsda_destination,
    ce.bsda_worker,
    ce.bsff,
    ce.bsff_emitter,
    ce.bsff_transporter,
    ce.bsff_destination,
    ce.bsdasri,
    ce.bsdasri_emitter,
    ce.bsdasri_transporter,
    ce.bsdasri_destination,
    ce.bsvhu,
    ce.bsvhu_emitter,
    ce.bsvhu_transporter,
    ce.bsvhu_destination,
    ce.texs_dd,
    ce.texs_dd_emitter,
    ce.texs_dd_transporter,
    ce.texs_dd_destination,
    ce.dnd,
    ce.dnd_emitter,
    ce.dnd_destination,
    ce.texs,ce.texs_emitter,ce.texs_destination,
    ce.ssd,
    ce.pnttd,
    ce.processing_operations_bsdd,
    ce.processing_operations_bsdnd,
    ce.processing_operations_bsda,
    ce.processing_operations_bsff,
    ce.processing_operations_bsdasri,
    ce.processing_operations_bsvhu,
    ce.processing_operations_dnd,
    ce.processing_operations_texs,

    ce.waste_codes_bordereaux,
    ce.waste_codes_dnd_statements,
    ce.waste_codes_texs_statements,
    ce.waste_codes_processed,

    ce.code_commune_insee,
    ce.code_departement_insee,
    ce.code_region_insee,
    ce.adresse_td,
    ce.adresse_insee,
    ce.date_inscription,
    (c.is_dormant_since is not null)::Bool as is_dormant,

    ce.coords
FROM
    refined_zone_vigiedechets.cartographie_etablissements_geocoded ce
LEFT JOIN
    trusted_zone_trackdechets.company c ON ce.siret = c.siret
ORDER BY ce.siret
"""
BATCH_SIZE = 10000


def cleanup_duplicate_sirets(may_have_duplicates):
    """Take a list of dicts and remove those whose siret is duplicated"""
    seen_sirets = set()
    deduplicated = []
    duplicates = set()

    for item in may_have_duplicates:
        siret = item.get("siret")
        if siret not in seen_sirets:
            seen_sirets.add(siret)
            deduplicated.append(item)
        else:
            duplicates.add(siret)

    return deduplicated, duplicates


def clean_pd_val(val):
    """Cleanup pd rows for db insertion"""
    if isinstance(val, dt.datetime) and pd.isna(val):
        return None
    if isinstance(val, float) and pd.isnat(val):
        return None
    return val


class Command(BaseCommand):
    help = "Import CartoCompany data with pagination"

    def add_arguments(self, parser):
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=BATCH_SIZE,
            help="Number of records to process in each batch",
        )

    def handle(self, *args, **options):
        chunk_size = options["chunk_size"]
        self.stdout.write("Deleting existing CartoCompany objects...")
        CartoCompany.objects.all().delete()

        count_query = "SELECT COUNT() FROM refined_zone_vigiedechets.cartographie_etablissements_geocoded"

        count_df = build_query(count_query)
        total_count = count_df.item()

        self.stdout.write(f"Found {total_count} records to import")

        offset = 0
        imported_count = 0
        total_duplicate_count = 0
        total_existing_count = 0
        total_failed_count = 0
        already_created_sirets = set()

        while offset < total_count:
            paginated_query = f"{BASE_QUERY} LIMIT {chunk_size} OFFSET {offset}"

            self.stdout.write(f"Processing records {offset + 1} to {min(offset + chunk_size, total_count)}")

            companies_df = build_query(paginated_query)

            companies_dicts = companies_df.to_dicts()
            dedup_companies_dicts, duplicate_sirets = cleanup_duplicate_sirets(companies_dicts)

            total_duplicate_count += len(duplicate_sirets)
            if duplicate_sirets:
                self.stdout.write(
                    self.style.WARNING(f"Skipped {len(duplicate_sirets)} duplicates: {sorted(duplicate_sirets)}")
                )

            refined_companies_dicts = [
                dct for dct in dedup_companies_dicts if dct["siret"] not in already_created_sirets
            ]

            skipped_existing = [
                dct["siret"] for dct in dedup_companies_dicts if dct["siret"] in already_created_sirets
            ]
            total_existing_count += len(skipped_existing)
            if skipped_existing:
                self.stdout.write(
                    self.style.WARNING(f"Skipped {len(skipped_existing)} already existing: {sorted(skipped_existing)}")
                )

            companies_dicts_without_nan = [{k: clean_pd_val(v) for k, v in e.items()} for e in refined_companies_dicts]
            data = [CartoCompany(**c) for c in companies_dicts_without_nan]

            created = CartoCompany.objects.bulk_create(data)
            # Update in-memory set with newly created companies
            already_created_sirets.update(obj.siret for obj in created)
            imported_count += len(created)
            self.stdout.write(f"Imported {len(created)} companies (total: {imported_count}/{total_count})")

            offset += chunk_size

        self.stdout.write(
            f"Summary — created: {imported_count}, skipped duplicates: {total_duplicate_count}, "
            f"skipped existing: {total_existing_count}, failed: {total_failed_count}"
        )
        self.stdout.write(self.style.SUCCESS(f"Successfully imported {imported_count} companies"))
