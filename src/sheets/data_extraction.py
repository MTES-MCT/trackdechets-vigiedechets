from typing import Any, Union
from zoneinfo import ZoneInfo

import polars as pl
from sqlalchemy.sql import text

from sheets.datawarehouse import get_wh_sqlachemy_engine

from .queries import (
    sql_bsda_query_str,
    sql_bsda_transporter_query_str,
    sql_bsdasri_query_str,
    sql_bsdd_non_dangerous_query_str,
    sql_bsdd_non_dangerous_transporter_query_str,
    sql_bsdd_query_str,
    sql_bsdd_transporter_query_str,
    sql_bsff_packagings_query_str,
    sql_bsff_query_str,
    sql_bsff_transporter_query_str,
    sql_bsvhu_query_str,
    sql_company_query_str,
    sql_get_broker_receipt_id_data,
    sql_get_eco_organisme_partners_data,
    sql_get_gistrid_data,
    sql_get_icpe_data,
    sql_get_icpe_item_data,
    sql_get_incoming_excavated_land_data,
    sql_get_incoming_ndw_data,
    sql_get_linked_companies_data,
    sql_get_outgoing_excavated_land_data,
    sql_get_outgoing_ndw_data,
    sql_get_ssd_data,
    sql_get_trader_receipt_id_data,
    sql_get_transporter_receipt_id_data_str,
    sql_get_vhu_agrement_data,
    sql_revised_bsda_query_str,
    sql_revised_bsdasri_query_str,
    sql_revised_bsdd_query_str,
)

query_types = {
    "id": pl.String,
    "readable_id": pl.String,
    "created_at": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "sent_at": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "received_at": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "processed_at": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "worker_work_signature_date": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "emitter_emission_signature_date": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "emitter_company_siret": pl.String,
    "emitter_company_address": pl.String,
    "recipient_company_siret": pl.String,
    "waste_details_quantity": pl.Float64,
    "quantity_received": pl.Float64,
    "quantity_refused": pl.Float64,
    "waste_code": pl.String,
    "waste_name": pl.String,
    "processing_operation_code": pl.String,
    "status": pl.String,
    "no_traceability": pl.Boolean,
    "waste_pop": pl.Boolean,
    "is_dangerous": pl.Boolean,
    "worksite_name": pl.String,
    "worksite_address": pl.String,
    "next_destination_company_siret": pl.String,
    "next_destination_company_name": pl.String,
    "next_destination_company_country": pl.String,
    "next_destination_company_vat_number": pl.String,
    "next_destination_processing_operation": pl.String,
    "eco_organisme_siret": pl.String,
    "bs_id": pl.String,
    "transporter_company_siret": pl.String,
    "transporter_number_plate": pl.List(inner=pl.String),
    "transporter_transport_mode": pl.String,
    "siret": pl.String,
    "name": pl.String,
    "address": pl.String,
    "company_types": pl.List(inner=pl.String),
    "transporter_receipt_id": pl.String,
    "trader_receipt_id": pl.String,
    "eco_organisme_agreements": pl.List(inner=pl.String),
    "broker_receipt_id": pl.String,
    "vhu_agrement_demolisseur_id": pl.String,
    "vhu_agrement_broyeur_id": pl.String,
    "collector_types": pl.List(inner=pl.String),
    "waste_processor_types": pl.List(inner=pl.String),
    "has_enabled_registry_dnd_from_bsd_since": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "eco_organisme_partners_ids": pl.List(inner=pl.String),
    "emitter_is_private_individual": pl.Boolean,
    "volume": pl.Float64,
    "bsff_id": pl.String,
    "acceptation_weight": pl.Float64,
    "weight": pl.Float64,
    "comment": pl.String,
    "is_canceled": pl.Boolean,
    "code_aiot": pl.String,
    "rubrique": pl.String,
    "quantite": pl.Float64,
    "unite": pl.String,
    "receipt_number": pl.String,
    "validity_limit": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "department": pl.String,
    "day_of_processing": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "processed_quantity": pl.Float64,
    "authorized_quantity": pl.Float64,
    "target_quantity": pl.Float64,
    "numero_notification": pl.String,
    "type_dossier": pl.String,
    "numero_gistrid_notifiant": pl.String,
    "siret_notifiant": pl.String,
    "nom_notifiant": pl.String,
    "pays_notifiant": pl.String,
    "numero_gistrid_installation_traitement": pl.String,
    "siret_installation_traitement": pl.String,
    "nom_installation_traitement": pl.String,
    "pays_installation_traitement": pl.String,
    "somme_quantites_recues": pl.Float64,
    "nombre_transferts_receptionnes": pl.Int64,
    "date_autorisee_debut_transferts": pl.String,
    "date_autorisee_fin_transferts": pl.String,
    "code_d_r": pl.String,
    "code_ced": pl.String,
    "weight_value": pl.Float64,
    "transporters_org_ids": pl.List(inner=pl.String),
    "waste_description": pl.String,
    "reception_date": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "dispatch_date": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "destination_company_org_id": pl.String,
    "operation_date": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "acceptation_date": pl.Datetime(time_zone=ZoneInfo("Europe/Paris")),
    "worker_company_siret": pl.String,
    "emitter_company_name": pl.String,
    "emitter_waste_weight_is_estimate": pl.Boolean,
    "refusal_reason": pl.String,
    "is_vhu_company": pl.Boolean,
}


def build_query(
    query_str,
    query_params: dict[str, Any] | None = None,
    date_columns=None,
    dtypes: dict[str, Any] | None = None,
):
    wh_engine = get_wh_sqlachemy_engine()

    if query_params:
        # Bind parameters directly to the query for SQLAlchemy 2.0+ compatibility
        query = text(query_str).bindparams(**query_params)
    else:
        query = text(query_str)

    df = pl.read_database(query=query, connection=wh_engine, schema_overrides=query_types)

    # if date_columns is not None:
    #     for col in date_columns:
    #         if col in df.columns:
    #             df[col] = pd.to_datetime(df[col], utc=True, errors="coerce").dt.tz_convert(None)

    return df


def build_bsdd_query(
    siret: str,
) -> pl.LazyFrame:
    df = build_query(
        sql_bsdd_query_str,
        query_params={
            "siret": siret,
        },
    )

    return df.lazy()


def build_bsdd_non_dangerous_query(
    siret: str,
) -> pl.LazyFrame:
    df = build_query(
        sql_bsdd_non_dangerous_query_str,
        query_params={
            "siret": siret,
        },
    )

    return df.lazy()


def build_revised_bsdd_query(
    company_id: str,
):
    df = build_query(
        sql_revised_bsdd_query_str,
        query_params={
            "company_id": company_id,
        },
    )

    return df.lazy()


def build_bsdd_transporter_query(
    siret: str,
):
    df = build_query(
        sql_bsdd_transporter_query_str,
        query_params={
            "siret": siret,
        },
    )

    return df.lazy()


def build_bsdd_non_dangerous_transporter_query(
    siret: str,
):
    df = build_query(
        sql_bsdd_non_dangerous_transporter_query_str,
        query_params={
            "siret": siret,
        },
    )

    return df.lazy()


def build_bsda_query(
    siret: str,
) -> pl.LazyFrame:
    return build_query(
        sql_bsda_query_str,
        query_params={
            "siret": siret,
        },
    ).lazy()


def build_bsda_transporter_query(
    siret: str,
):
    df = build_query(
        sql_bsda_transporter_query_str,
        query_params={
            "siret": siret,
        },
    )

    return df.lazy()


def build_revised_bsda_query(
    company_id: str,
):
    df = build_query(
        sql_revised_bsda_query_str,
        query_params={
            "company_id": company_id,
        },
    )

    return df.lazy()


def build_bsdasri_query(
    siret: str,
) -> pl.LazyFrame:
    return build_query(
        sql_bsdasri_query_str,
        query_params={
            "siret": siret,
        },
    ).lazy()


def build_revised_bsdasri_query(
    company_id: str,
):
    df = build_query(
        sql_revised_bsdasri_query_str,
        query_params={
            "company_id": company_id,
        },
    )

    return df.lazy()


def build_bsff_query(
    siret: str,
) -> pl.LazyFrame:
    return build_query(
        sql_bsff_query_str,
        query_params={
            "siret": siret,
        },
    ).lazy()


def build_bsff_packagings_query(
    siret: str,
) -> pl.LazyFrame:
    return build_query(
        sql_bsff_packagings_query_str,
        query_params={
            "siret": siret,
        },
        date_columns=["operation_date", "acceptation_date"],
    ).lazy()


def build_bsff_transporter_query(
    siret: str,
):
    df = build_query(
        sql_bsff_transporter_query_str,
        query_params={
            "siret": siret,
        },
    ).lazy()

    return df


def build_bsvhu_query(
    siret: str,
) -> pl.LazyFrame:
    return build_query(
        sql_bsvhu_query_str,
        query_params={
            "siret": siret,
        },
    ).lazy()


def build_query_company(siret, date_params=None):
    return build_query(
        sql_company_query_str,
        query_params={
            "siret": siret,
        },
        date_columns=date_params,
    ).lazy()


company_agreements_query_config = [
    {
        "name": "Récépissé Transporteur",
        "column": "transporter_receipt_id",
        "sql": sql_get_transporter_receipt_id_data_str,
    },
    {
        "name": "Récépissé Négociant",
        "column": "trader_receipt_id",
        "sql": sql_get_trader_receipt_id_data,
    },
    {
        "name": "Récépissé Courtier",
        "column": "broker_receipt_id",
        "sql": sql_get_broker_receipt_id_data,
    },
    {
        "name": "Agrément Démolisseur ",
        "column": "vhu_agrement_demolisseur_id",
        "sql": sql_get_vhu_agrement_data,
    },
    {
        "name": "Agrément Broyeur",
        "column": "vhu_agrement_broyeur_id",
        "sql": sql_get_vhu_agrement_data,
    },
]


def get_agreement_data(company_data_df: pl.LazyFrame) -> dict:
    res = {}

    for config in company_agreements_query_config:
        try:
            id_ = company_data_df.select(pl.col([config["column"]])).collect().item()
        except ValueError:
            id_ = None

        if id_ is not None:
            df = build_query(
                config["sql"],
                date_columns=["validity_limit"],
                query_params={"id": id_},
            )
            if len(df) != 0:
                res[config["name"]] = df.lazy()
    return res


def get_icpe_data(siret: str) -> Union[pl.LazyFrame, None]:
    icpe_data = build_query(
        sql_get_icpe_data,
        query_params={
            "siret": siret,
        },
    )

    if len(icpe_data):
        return icpe_data.lazy()
    return None


def get_icpe_item_data(siret: str, rubrique: str) -> Union[pl.LazyFrame, None]:
    icpe_data = build_query(
        sql_get_icpe_item_data,
        query_params={"siret": siret, "rubrique": rubrique},
        date_columns=["day_of_processing"],
    )

    if len(icpe_data):
        return icpe_data.lazy()
    return None


def get_linked_companies_data(siret: str) -> Union[pl.LazyFrame, None]:
    linked_companies_data = build_query(
        sql_get_linked_companies_data,
        query_params={
            "siret": siret,
        },
    )

    if len(linked_companies_data):
        return linked_companies_data.lazy()
    return None


def get_gistrid_data(siret: str) -> Union[pl.LazyFrame, None]:
    gistrid_data = build_query(
        sql_get_gistrid_data,
        query_params={
            "siret": siret,
        },
    )

    if len(gistrid_data):
        return gistrid_data.lazy()
    return None


def get_registries_ndw_data(siret: str) -> tuple[pl.LazyFrame | None, pl.LazyFrame | None]:
    registries_ndw_incoming_data = build_query(
        sql_get_incoming_ndw_data,
        query_params={
            "siret": siret,
        },
        date_columns=["reception_date"],
    )

    registries_ndw_outgoing_data = build_query(
        sql_get_outgoing_ndw_data,
        query_params={
            "siret": siret,
        },
        date_columns=["dispatch_date"],
    )

    if all(len(e) == 0 for e in [registries_ndw_incoming_data, registries_ndw_outgoing_data]):
        return None, None
    return registries_ndw_incoming_data.lazy(), registries_ndw_outgoing_data.lazy()


def get_registries_excavated_land_data(siret: str) -> tuple[pl.LazyFrame | None, pl.LazyFrame | None]:
    registries_excavated_land_incoming_data = build_query(
        sql_get_incoming_excavated_land_data,
        query_params={
            "siret": siret,
        },
        date_columns=["reception_date"],
    )

    registries_excavated_land_outgoing_data = build_query(
        sql_get_outgoing_excavated_land_data,
        query_params={
            "siret": siret,
        },
        date_columns=["dispatch_date"],
    )

    if all(len(e) == 0 for e in [registries_excavated_land_incoming_data, registries_excavated_land_outgoing_data]):
        return None, None
    return registries_excavated_land_incoming_data.lazy(), registries_excavated_land_outgoing_data.lazy()


def get_ssd_data(siret: str) -> Union[pl.LazyFrame, None]:
    ssd_data = build_query(
        sql_get_ssd_data,
        query_params={
            "siret": siret,
        },
        date_columns=["dispatch_date"],
    )

    if len(ssd_data):
        return ssd_data.lazy()
    return None


def get_eco_organisme_partners_data(partner_ids: list[str]) -> list[dict]:
    """Get eco-organisme partners data from their SIRETs.

    Parameters
    ----------
    partner_ids : list[str]
        List of company ids to look up.

    Returns
    -------
    list[dict]
        List of dicts with 'siret' and 'name' keys.
    """

    df = build_query(sql_get_eco_organisme_partners_data, query_params={"partner_ids": tuple(partner_ids)})

    return [{"name": row["name"], "siret": row["siret"]} for row in df.iter_rows(named=True)]
