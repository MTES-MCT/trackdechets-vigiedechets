icpe_installations_sql = """
select 
    code_aiot,
    raison_sociale,
    siret,
    rubrique,
    quantite_autorisee,
    unite,
    latitude,
    longitude,
    adresse1,
    adresse2,
    code_postal,
    commune
from 
    refined_zone_vigiedechets.installations_icpe_2024
"""

icpe_installations_waste_processed_sql = """
select
    *
from
    refined_zone_vigiedechets.icpe_installations_daily_processed_waste
"""

icpe_departements_waste_processed_sql = """
select
    *
from
    refined_zone_vigiedechets.icpe_departements_daily_processed_waste
"""

icpe_regions_waste_processed_sql = """
select
    *
from
    refined_zone_vigiedechets.icpe_regions_daily_processed_waste
"""

icpe_france_waste_processed_sql = """
select
    *
from
    refined_zone_vigiedechets.icpe_france_daily_processed_waste
"""
