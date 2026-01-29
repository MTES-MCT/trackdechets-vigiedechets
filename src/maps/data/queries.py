import polars as pl

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
    refined_zone_vigiedechets.cartographie_icpe_installations
"""


icpe_installations_schema_overrides = {
    "code_aiot": pl.String,
    "siret": pl.String,
    "raison_sociale": pl.String,
    "rubrique": pl.String,
    "quantite_autorisee": pl.Float64,
    "unite": pl.String,
    "latitude": pl.Float64,
    "longitude": pl.Float64,
    "adresse1": pl.String,
    "adresse2": pl.String,
    "code_postal": pl.String,
    "commune": pl.String,
}


icpe_installations_waste_processed_sql = """
select
    code_aiot,
    rubrique,
    raison_sociale,
    siret,
    adresse1,
    adresse2,
    code_postal,
    commune,
    latitude,
    longitude,
    quantite_autorisee,
    unite,
    quantite_traitee,
    day_of_processing,
    quantite_objectif
from
    refined_zone_vigiedechets.cartographie_icpe_installations_daily_processed_waste
"""

icpe_installations_waste_processed_schema_overrides = {
    "code_aiot": pl.String,
    "siret": pl.String,
    "raison_sociale": pl.String,
    "rubrique": pl.String,
    "quantite_autorisee": pl.Float64,
    "quantite_objectif": pl.Float64,
    "quantite_traitee": pl.Float64,
    "unite": pl.String,
    "latitude": pl.Float64,
    "longitude": pl.Float64,
    "adresse1": pl.String,
    "adresse2": pl.String,
    "code_postal": pl.String,
    "commune": pl.String,
}

icpe_departements_waste_processed_sql = """
select
    code_departement_insee,
    nom_departement,
    code_region_insee,
    rubrique,
    day_of_processing,
    nombre_installations,
    quantite_traitee,
    quantite_autorisee
from
    refined_zone_vigiedechets.cartographie_icpe_departements_daily_processed_waste
"""

icpe_departements_waste_processed_schema_overrides = {
    "code_departement_insee": pl.String,
    "nom_departement": pl.String,
    "code_region_insee": pl.String,
    "rubrique": pl.String,
    "day_of_processing": pl.Date,
    "nombre_installations": pl.Int64,
    "quantite_traitee": pl.Float64,
    "quantite_autorisee": pl.Float64,
}

icpe_regions_waste_processed_sql = """
select
    code_region_insee,
    nom_region,
    rubrique,
    day_of_processing,
    nombre_installations,
    quantite_traitee,
    quantite_autorisee
from
    refined_zone_vigiedechets.cartographie_icpe_regions_daily_processed_waste
"""

icpe_regions_waste_processed_schema_overrides = {
    "code_region_insee": pl.String,
    "nom_region": pl.String,
    "rubrique": pl.String,
    "day_of_processing": pl.Date,
    "nombre_installations": pl.Int64,
    "quantite_traitee": pl.Float64,
    "quantite_autorisee": pl.Float64,
}

icpe_france_waste_processed_sql = """
select
    rubrique,
    day_of_processing,
    nombre_installations,
    quantite_traitee,
    quantite_autorisee
from
    refined_zone_vigiedechets.cartographie_icpe_france_daily_processed_waste
"""

icpe_france_waste_processed_schema_overrides = {
    "rubrique": pl.String,
    "day_of_processing": pl.Date,
    "nombre_installations": pl.Int64,
    "quantite_traitee": pl.Float64,
    "quantite_autorisee": pl.Float64,
}
