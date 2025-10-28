from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from sheets.constants import BSDA, BSDASRI, BSDD, BSFF


from ..graph_processors.html_components_processors import (
    BsdCanceledTableProcessor,
)  # Remplace "your_module" par le bon module

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def sample_data_bsdd():
    data = {
        "id": ["bsdd-1", "bsdd-2", "bsdd-3", "bsdd-4"],
        "recipient_company_siret": ["12345678900011", "12345678900011", "98765432100022", "12345678900011"],
        "emitter_company_siret": ["98765432100022", "98765432100022", "12345678900011", "98765432100011"],
        "received_at": [
            datetime(2024, 1, 10, tzinfo=tz),
            datetime(2024, 2, 15, tzinfo=tz),
            datetime(2024, 3, 20, tzinfo=tz),
            datetime(2024, 4, 25, tzinfo=tz),
        ],
        "readable_id": ["BSDD0001", "BSDD0002", "BSDD0003", "BSDD0004"],
        "created_at": [
            datetime(2024, 1, 1, 8, 0, tzinfo=tz),
            datetime(2024, 2, 1, 8, 0, tzinfo=tz),
            datetime(2024, 3, 1, 8, 0, tzinfo=tz),
            datetime(2024, 4, 1, 8, 0, tzinfo=tz),
        ],
        "sent_at": [
            datetime(2024, 1, 5, 9, 0, tzinfo=tz),
            datetime(2024, 2, 10, 9, 0, tzinfo=tz),
            datetime(2024, 3, 15, 9, 0, tzinfo=tz),
            datetime(2024, 4, 20, 9, 0, tzinfo=tz),
        ],
        "processed_at": [
            datetime(2024, 1, 15, 10, 0, tzinfo=tz),
            datetime(2024, 2, 20, 10, 0, tzinfo=tz),
            datetime(2024, 3, 25, 10, 0, tzinfo=tz),
            datetime(2024, 4, 30, 10, 0, tzinfo=tz),
        ],
        "signed_at": [
            datetime(2024, 1, 15, 10, 0, tzinfo=tz),
            datetime(2024, 2, 20, 10, 0, tzinfo=tz),
            datetime(2024, 3, 25, 10, 0, tzinfo=tz),
            datetime(2024, 4, 30, 10, 0, tzinfo=tz),
        ],
        "emitter_company_address": ["1 Rue A, Paris", "2 Rue B, Lyon", "3 Rue C, Lille", "4 Rue D, Nantes"],
        "waste_details_quantity": [10.0, 20.0, 30.0, 40.0],
        "quantity_received": [9.0, 20.0, 28.0, 0.0],
        "quantity_refused": [1.0, None, 2.0, 40.0],
        "waste_code": ["20 01 01*", "20 01 02", "20 01 03*", "20 01 08*"],
        "waste_name": ["Solvant A", "Solvant B", "Solvant C", "Solvant D"],
        "processing_operation_code": ["D10", "R1", "D9", "R12"],
        "status": ["PROCESSED", "PROCESSED", "REFUSED", "REFUSED"],
        "no_traceability": [False, False, False, True],
        "waste_pop": [True, False, True, False],
        "is_dangerous": [True, False, True, False],
        "worksite_name": ["Site A", "Site B", None, "Site D"],
        "worksite_address": ["1 Ch. A, Paris", "2 Ch. B, Lyon", None, "4 Ch. D, Nantes"],
        "next_destination_company_siret": [None, "22222222200011", None, "44444444400044"],
        "next_destination_company_name": [None, "NextCo B", None, "NextCo D"],
        "next_destination_company_country": [None, "FR", None, "FR"],
        "next_destination_company_vat_number": [None, "VATB", None, "VATD"],
        "next_destination_processing_operation": [None, "R3", None, "R1"],
        "eco_organisme_siret": [None, None, None, None],
        "comment": [None, None, "Refusal reason 1", "Refusal reason 2"],        
    }
    return pl.DataFrame(
        data,
        schema_overrides={
            "id": pl.String,
            "quantity_received": pl.Float64,
            "emitter_company_siret": pl.String,
            "recipient_company_siret": pl.String,
            "waste_code": pl.String,
            "updated_at": pl.Datetime(time_unit="us", time_zone="Europe/Paris"),
            "comment": pl.String,
            "readable_id": pl.String,
            "waste_name": pl.String,
            "quantity_refused": pl.Float64,
        },
    ).lazy()


@pytest.fixture
def sample_data_bsda():
    data = {
        "id": ["bsda-1", "bsda-2", "bsda-3", "bsda-4"],
        "created_at": [
            datetime(2024, 1, 1, 8, 0, tzinfo=tz),
            datetime(2024, 2, 1, 9, 0, tzinfo=tz),
            datetime(2024, 3, 1, 10, 0, tzinfo=tz),
            datetime(2024, 4, 1, 11, 0, tzinfo=tz),
        ],
        "emitter_emission_signature_date": [
            datetime(2024, 1, 2, 10, 30, 0, tzinfo=tz),
            datetime(2024, 2, 2, 10, 30, 0, tzinfo=tz),
            datetime(2024, 3, 2, 11, 30, 0, tzinfo=tz),
            None,
        ],
        "worker_work_signature_date": [
            datetime(2024, 1, 3, 11, 0, 0, tzinfo=tz),
            None,
            datetime(2024, 3, 3, 12, 0, 0, tzinfo=tz),
            datetime(2024, 4, 3, 13, 0, 0, tzinfo=tz),
        ],
        "sent_at": [
            datetime(2024, 1, 3, 12, 30, 0, tzinfo=tz),
            datetime(2024, 2, 3, 12, 30, 0, tzinfo=tz),
            datetime(2024, 3, 3, 13, 30, 0, tzinfo=tz),
            datetime(2024, 4, 3, 14, 30, 0, tzinfo=tz),
        ],
        "received_at": [
            datetime(2024, 1, 4, 8, 0, 0, tzinfo=tz),
            None,
            datetime(2024, 3, 4, 9, 0, 0, tzinfo=tz),
            datetime(2024, 4, 4, 10, 0, 0, tzinfo=tz),
        ],
        "processed_at": [
            datetime(2024, 1, 5, 15, 0, 0, tzinfo=tz),
            datetime(2024, 2, 5, 16, 0, 0, tzinfo=tz),
            None,
            datetime(2024, 4, 5, 17, 0, 0, tzinfo=tz),
        ],
        "emitter_company_siret": ["55555555500029", "66666666600030", "77777777700031", "88888888800032"],
        "emitter_company_name": ["Company Emitter 1", "Company Emitter 2", "Company Emitter 3", "Company Emitter 4"],
        "emitter_company_address": [
            "10 Rue des Fleurs, Paris",
            "20 Rue des Pommiers, Lyon",
            "30 Rue des Platanes, Lille",
            "40 Rue des Erables, Toulouse",
        ],
        "recipient_company_siret": ["12345678900011", "12345678900011", "12345678900011", "12345678900011"],
        "waste_details_quantity": [100.0, 50.0, 200.0, 120.0],
        "quantity_received": [98.0, None, 197.0, 119.0],
        "waste_code": ["18 01 03*", "18 01 02", "18 01 06*", "18 01 08*"],
        "waste_name": ["Déchets chimiques", "Déchets ménagers", "Déchets infectieux", "Déchets pharmaceutiques"],
        "processing_operation_code": ["D15", "R12", "D10", "R13"],
        "status": ["PROCESSED", "PROCESSED", "REFUSED", "PROCESSED"],
        "waste_pop": [True, False, True, False],
        "worksite_name": ["Chantier Alpha", "Chantier Beta", None, "Chantier Delta"],
        "worksite_address": ["1 rue du Travail, Nice", None, "3 chemin P, Pau", "4 avenue des Tests, Marseille"],
        "worker_company_siret": ["12345678900011", None, "22222222200011", "33333333300012"],
        "emitter_is_private_individual": [False, False, True, False],
        "eco_organisme_siret": [None, "44444444400044", None, None],
        "comment": [None, None, "Comment 1", None],
        "destination_reception_waste_refusal_reason": [None, None, "Refusal reason 1", None],
    }
    return pl.DataFrame(
        data,
        schema_overrides={
            "id": pl.String,
            "quantity_received": pl.Float64,
            "emitter_company_siret": pl.String,
            "recipient_company_siret": pl.String,
            "waste_code": pl.String,
            "updated_at": pl.Datetime(time_unit="us", time_zone="Europe/Paris"),
            "comment": pl.String,
        },
    ).lazy()


@pytest.fixture
def sample_data_bsdasri():
    data = {
        "id": ["bsdasri-1", "bsdasri-2", "bsdasri-3"],
        "created_at": [
            datetime(2024, 10, 15, 8, 10, 48, tzinfo=tz),
            datetime(2024, 11, 22, 9, 12, 34, tzinfo=tz),
            datetime(2024, 12, 1, 15, 44, 11, tzinfo=tz),
        ],
        "sent_at": [datetime(2024, 10, 16, 10, 0, 0, tzinfo=tz), None, datetime(2024, 12, 2, 8, 35, 50, tzinfo=tz)],
        "received_at": [
            datetime(2024, 10, 16, 14, 45, 0, tzinfo=tz),
            None,
            datetime(2024, 12, 2, 12, 0, 33, tzinfo=tz),
        ],
        "processed_at": [datetime(2024, 10, 17, 7, 21, 0, tzinfo=tz), None, None],
        "emitter_company_siret": ["71138119200016", "35512387600099", "49016873200053"],
        "emitter_company_address": ["22 rue Foch, Dijon", "4 avenue du Midi, Nice", None],
        "recipient_company_siret": ["12345678900011", "12345678900011", "12345678900011"],
        "waste_details_quantity": [180.5, 62, 245],
        "quantity_received": [180.5, None, 200],
        "quantity_refused": [None, None, 45],
        "volume": [2.3, 1.1, 4.7],
        "waste_code": ["18 01 03*", "18 01 06*", "20 01 27*"],
        "processing_operation_code": ["D15", "R13", "D10"],
        "status": ["PROCESSED", "INITIAL", "REFUSED"],
        "transporter_transport_mode": ["ROAD", "RAIL", "ROAD"],
        "transporter_company_siret": ["62131276300081", "47816734500020", "51283678900091"],
        "eco_organisme_siret": [None, "71002233400010", None],
        "comment": ["Refusal reason 1", None, "Refusal reason 2"],
    }
    
    return pl.DataFrame(
        data,
        schema_overrides={
            "id": pl.String,
            "quantity_received": pl.Float64,
            "emitter_company_siret": pl.String,
            "recipient_company_siret": pl.String,
            "waste_code": pl.String,
            "updated_at": pl.Datetime(time_unit="us", time_zone="Europe/Paris"),
            "comment": pl.String,
            "readable_id": pl.String,
            "waste_name": pl.String,
            "quantity_refused": pl.Float64,
        },
    ).lazy()


@pytest.fixture
def sample_data_bsff():
    """ """

    data = {
        "id": ["bsff-1", "bsff-2", "bsff-3"],
        "created_at": [
            datetime(2024, 1, 10, 8, 0, tzinfo=tz),
            datetime(2024, 2, 10, 9, 0, tzinfo=tz),
            datetime(2024, 3, 10, 10, 0, tzinfo=tz),
        ],
        "sent_at": [datetime(2024, 1, 12, 10, 0, tzinfo=tz), None, datetime(2024, 3, 12, 11, 0, tzinfo=tz)],
        "received_at": [datetime(2024, 1, 13, 12, 0, tzinfo=tz), datetime(2024, 2, 13, 13, 0, tzinfo=tz), None],
        "emitter_company_siret": ["19988777600011", "24358764500022", "38512649800033"],
        "emitter_company_address": [
            "55 Bd Voltaire, Paris",
            "12 Rue Victor Hugo, Marseille",
            "99 Av République, Bordeaux",
        ],
        "recipient_company_siret": ["12345678900011", "12345678900011", "12345678900011"],
        "waste_details_quantity": [120.0, 80.5, 95.1],
        "waste_code": ["14 06 01*", "14 06 02*", "14 06 03*"],
        "status": [
            "PROCESSED",
            "REFUSED",
            "PROCESSED",
        ],
    }
    return pl.DataFrame(
        data,
        schema_overrides={
            "id": pl.String,
            "quantity_received": pl.Float64,
            "emitter_company_siret": pl.String,
            "recipient_company_siret": pl.String,
            "waste_code": pl.String,
            "updated_at": pl.Datetime(time_unit="us", time_zone="Europe/Paris"),
            "comment": pl.String,
            "readable_id": pl.String,
            "waste_name": pl.String,
            "quantity_refused": pl.Float64,
        },
    ).lazy()


@pytest.fixture
def sample_revised_data():
    """List of revised data for the canceled bordereaux"""

    data = {
        "bs_id": ["bsdd-1", "bsda-2", "bsdasri-3"],
        "created_at": [
            datetime(2024, 1, 10, 8, 0, tzinfo=tz),
            datetime(2024, 2, 10, 9, 0, tzinfo=tz),
            datetime(2024, 3, 10, 10, 0, tzinfo=tz),
        ],
        "updated_at": [
            datetime(2024, 1, 12, 10, 0, tzinfo=tz),
            datetime(2024, 2, 10, 10, 0, tzinfo=tz),
            datetime(2024, 3, 12, 11, 0, tzinfo=tz),
        ],
        "comment": [None, "C1", "C2"],
        "is_canceled": [True, True, True],
    }
    return pl.DataFrame(
        data,
        schema_overrides={
            "bs_id": pl.String,
            "created_at": pl.Datetime(time_unit="us", time_zone="Europe/Paris"),
            "updated_at": pl.Datetime(time_unit="us", time_zone="Europe/Paris"),
            "comment": pl.String,
            "is_canceled": pl.Boolean,
        },
    ).lazy()


@pytest.fixture
def data_date_interval():
    return (datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 12, 31, tzinfo=tz))
