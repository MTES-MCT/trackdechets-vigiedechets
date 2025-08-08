import datetime as dt

import pandas as pd
from django.core.management.base import BaseCommand

from sheets.data_extraction import build_query

from ...models import CartoCompany

BASE_QUERY = """
SELECT
    siret,
    nom_etablissement,
    profils,
    profils_collecteur,
    profils_installation,
    profils_installation_vhu,
    bsdd,
    bsdd_emitter,
    bsdd_transporter,
    bsdd_destination,
    bsdnd,
    bsdnd_emitter,
    bsdnd_transporter,
    bsdnd_destination,
    bsda,
    bsda_emitter,
    bsda_transporter,
    bsda_destination,
    bsda_worker,
    bsff,
    bsff_emitter,
    bsff_transporter,
    bsff_destination,
    bsdasri,
    bsdasri_emitter,
    bsdasri_transporter,
    bsdasri_destination,
    bsvhu,
    bsvhu_emitter,
    bsvhu_transporter,
    bsvhu_destination,
    texs_dd,
    texs_dd_emitter,
    texs_dd_transporter,
    texs_dd_destination,
    dnd,
    dnd_emitter,
    dnd_destination,
    texs,texs_emitter,texs_destination,
    ssd,
    pnttd,
    processing_operations_bsdd,
    processing_operations_bsdnd,
    processing_operations_bsda,
    processing_operations_bsff,
    processing_operations_bsdasri,
    processing_operations_bsvhu,
    processing_operations_dnd,
    processing_operations_texs,

    waste_codes_bordereaux,
    waste_codes_dnd_statements,
    waste_codes_texs_statements,
    waste_codes_processed,

    code_commune_insee,
    code_departement_insee,
    code_region_insee,
    adresse_td,
    adresse_insee,
    date_inscription,

    coords
FROM
    refined_zone_vigiedechets.cartographie_des_etablissements_geocoded
ORDER BY siret
"""
BATCH_SIZE = 10000


def cleanup_duplicate_sirets(may_have_duplicates):
    """Take a list of dicts and remove those whose siret is duplicated"""
    seen_sirets = set()
    deduplicated = []

    for item in may_have_duplicates:
        siret = item.get("siret")
        if siret not in seen_sirets:
            seen_sirets.add(siret)
            deduplicated.append(item)

    return deduplicated


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

        count_query = "SELECT COUNT() FROM refined_zone_vigiedechets.cartographie_des_etablissements_geocoded"

        count_df = build_query(count_query)
        total_count = count_df.iloc[0, 0]

        self.stdout.write(f"Found {total_count} records to import")

        offset = 0
        imported_count = 0

        while offset < total_count:
            paginated_query = f"{BASE_QUERY} LIMIT {chunk_size} OFFSET {offset}"

            self.stdout.write(f"Processing records {offset + 1} to {min(offset + chunk_size, total_count)}")

            companies_df = build_query(paginated_query)

            companies_dicts = companies_df.to_dict(orient="records")
            dedup_companies_dicts = cleanup_duplicate_sirets(companies_dicts)

            already_existing_sirets = CartoCompany.objects.all().values_list("siret", flat=True)
            refined_companies_dicts = [
                dct for dct in dedup_companies_dicts if dct["siret"] not in already_existing_sirets
            ]

            companies_dicts_without_nan = [{k: clean_pd_val(v) for k, v in e.items()} for e in refined_companies_dicts]

            data = [CartoCompany(**c) for c in companies_dicts_without_nan]
            created = CartoCompany.objects.bulk_create(data)

            imported_count += len(created)

            self.stdout.write(f"Imported {len(created)} companies (total: {imported_count}/{total_count})")

            offset += chunk_size

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {imported_count} companies"))
