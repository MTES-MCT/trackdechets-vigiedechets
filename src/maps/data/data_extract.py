import json
import logging
import time


import polars as pl
import polars.selectors as cs
from django.conf import settings
from sqlalchemy import create_engine
from sheets.ssh import get_tunnel_port, ssh_tunnel

from ..utils import format_waste_codes

SQL_PATH = settings.BASE_DIR / "data" / "sql"
STATIC_DATA_PATH = settings.BASE_DIR / "data" / "static"

logger = logging.getLogger(__name__)

FLOAT_COLUMNS = [
    "quantite_tracee",
    "quantite_emise",
    "quantite_envoyee",
    "quantite_recue",
    "quantite_traitee",
    "quantite_traitee_operations_non_finales",
    "quantite_traitee_operations_finales",
    "quantite_produite",
]


def run_query_polars(sql_string: str, schema_overrides: dict = None) -> pl.DataFrame:
    """
    Executes a SQL query to fetch data from the database and returns it as a Polars DataFrame.

    Parameters
    ----------
    sql_string : str
        The SQL query string used to fetch data from the database.
    schema_overrides : dict, optional
        A dictionary specifying any schema overrides (polars types) for the query result. Defaults to None.

    Returns
    -------
    pl.DataFrame
        A Polars DataFrame containing the data fetched from the database.

    Notes
    -----
    This function uses SSH tunneling to securely connect to the ClickHouse database.
    It relies on the `ssh_tunnel` context manager to establish and close the SSH connection.
    The function also logs the duration of the query execution using the `logger`.
    """
    started_time = time.time()

    ssh_tunnel(settings)
    local_port = get_tunnel_port()
    dwh_ssh_local_bind_host = settings.DWH_SSH_LOCAL_BIND_HOST

    SQLALCHEMY_DATABASE_URL = (
        f"clickhouse+native://{settings.DWH_USERNAME}:{settings.DWH_PASSWORD}@{dwh_ssh_local_bind_host}:{local_port}"
    )

    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    data_df = pl.read_database(sql_string, connection=engine, schema_overrides=schema_overrides)

    logger.info(
        "Loading stats duration: %s (query : %s)",
        time.time() - started_time,
        sql_string,
    )

    return data_df


def extract_dataset(sql_string: str, schema_overrides: dict | None = None) -> pl.DataFrame:
    """
    Extracts a dataset from the database using an SQL query and performs type casting on specified columns.

    Parameters
    ----------
    sql_string : str
        The SQL query string used to fetch data from the database.
    schema_overrides : dict, optional
        A dictionary specifying any schema overrides (polars types) for the query result. Defaults to None.

    Returns
    -------
    pl.DataFrame
        A Polars DataFrame containing the extracted data with specified columns cast to Float64 if they are originally of type String and listed in FLOAT_COLUMNS.

    Notes
    -----
    This function assumes that `FLOAT_COLUMNS` is a predefined list of column names that need to be cast to Float64.
    It also relies on the `run_query` function to execute the SQL query and fetch the data.
    """

    data_df = run_query_polars(sql_string, schema_overrides)
    for colname, data_type in data_df.schema.items():
        if (data_type == pl.String) and (colname in FLOAT_COLUMNS):
            data_df = data_df.with_columns(pl.col(colname).cast(pl.Float64))

    return data_df


def get_processing_operation_codes_data() -> pl.DataFrame:
    """
    Returns description for each processing operation codes.

    Returns
    --------
    DataFrame
        DataFrame with processing operations codes and description.
    """
    data = run_query_polars("SELECT * FROM trusted_zone_referentials.codes_operations_traitements")
    return data


def get_departement_geographical_data() -> pl.DataFrame:
    """
    Returns INSEE department geographical data.

    Returns
    --------
    DataFrame
        DataFrame with INSEE department geographical data.
    """
    data = run_query_polars("SELECT * FROM trusted_zone_insee.code_geo_departements")

    return data


def get_waste_nomenclature_data() -> pl.DataFrame:
    """
    Returns waste nomenclature data.

    Returns
    --------
    DataFrame
        DataFrame with waste nomenclature data.
    """
    data = run_query_polars("SELECT * FROM trusted_zone_referentials.codes_dechets")
    return data


def get_waste_code_hierarchical_nomenclature() -> list[dict]:
    """
    Returns waste code nomenclature in a hierarchical way, to use with tree components.

    Returns
    --------
    list of dicts
        Each dict contains the data necessary for the TreeComponent along with childrens.
    """
    with (STATIC_DATA_PATH / "waste_codes.json").open() as f:
        waste_code_hierarchy = json.load(f)

    return format_waste_codes(waste_code_hierarchy, add_top_level=True)
