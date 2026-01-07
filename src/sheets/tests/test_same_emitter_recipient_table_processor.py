from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl

from sheets.constants import BSDA, BSDD

from ..graph_processors.html_components import SameEmitterRecipientTableProcessor


def test_same_emitter_recipient_table_processor_build_returns_only_matching_rows():
    """GIVEN bordereaux and transporter data
    WHEN building the same-emitter/recipient table
    THEN it returns only rows where emitter==recipient, worksite address exists, and sent_at is within the interval.
    """

    tz = ZoneInfo("Europe/Paris")
    data_date_interval = (datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 12, 31, tzinfo=tz))

    company_siret = "12345678900011"

    bsdd_df = pl.LazyFrame(
        {
            "id": ["bsdd-1", "bsdd-2"],
            "readable_id": ["BSDD-0001", "BSDD-0002"],
            "sent_at": [datetime(2024, 2, 1, tzinfo=tz), datetime(2024, 2, 2, tzinfo=tz)],
            "received_at": [datetime(2024, 2, 5, tzinfo=tz), datetime(2024, 2, 6, tzinfo=tz)],
            "quantity_received": [10.0, 5.0],
            "waste_code": ["20 01 01*", "20 01 01*"],
            "waste_name": ["Solvant", "Solvant"],
            "worksite_name": ["Site A", "Site B"],
            "worksite_address": ["1 rue A", None],
            "emitter_company_siret": [company_siret, company_siret],
            "recipient_company_siret": [company_siret, company_siret],
        }
    )

    bsda_df = pl.LazyFrame(
        {
            "id": ["bsda-1"],
            "received_at": [datetime(2024, 3, 10, tzinfo=tz)],
            "quantity_received": [7.0],
            "waste_code": ["18 01 02"],
            "waste_name": ["Déchets ménagers"],
            "worksite_name": ["Chantier C"],
            "worksite_address": ["3 rue C"],
            "emitter_company_siret": [company_siret],
            "recipient_company_siret": [company_siret],
        }
    )

    bsdd_transport_df = pl.LazyFrame(
        {
            "bs_id": ["bsdd-1", "bsdd-2"],
            "sent_at": [datetime(2024, 2, 1, tzinfo=tz), datetime(2024, 2, 2, tzinfo=tz)],
            "transporter_company_siret": ["99999999900099", "99999999900099"],
        }
    )
    bsda_transport_df = pl.LazyFrame(
        {
            "bs_id": ["bsda-1"],
            "sent_at": [datetime(2024, 3, 1, tzinfo=tz)],
            "transporter_company_siret": ["99999999900099"],
        }
    )

    processor = SameEmitterRecipientTableProcessor(
        bs_data_dfs={BSDD: bsdd_df, BSDA: bsda_df},
        transporters_data_dfs={BSDD: bsdd_transport_df, BSDA: bsda_transport_df},
        data_date_interval=data_date_interval,
    )

    result = processor.build()

    assert isinstance(result, list)
    assert {row["id"] for row in result} == {"bsdd-1", "bsda-1"}
    assert next(row for row in result if row["id"] == "bsda-1")["readable_id"] == "bsda-1"


def test_same_emitter_recipient_table_processor_build_returns_empty_dict_when_no_match():
    """GIVEN bordereaux that do not match filter criteria
    WHEN building the same-emitter/recipient table
    THEN it returns an empty dict.
    """

    tz = ZoneInfo("Europe/Paris")
    data_date_interval = (datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 12, 31, tzinfo=tz))

    bsdd_df = pl.LazyFrame(
        {
            "id": ["bsdd-1"],
            "readable_id": ["BSDD-0001"],
            "received_at": [datetime(2024, 2, 5, tzinfo=tz)],
            "quantity_received": [10.0],
            "waste_code": ["20 01 01*"],
            "waste_name": ["Solvant"],
            "worksite_name": ["Site A"],
            "worksite_address": [None],
            "emitter_company_siret": ["12345678900011"],
            "recipient_company_siret": ["12345678900011"],
        }
    )

    bsdd_transport_df = pl.LazyFrame(
        {
            "bs_id": ["bsdd-1"],
            "sent_at": [datetime(2024, 2, 1, tzinfo=tz)],
            "transporter_company_siret": ["99999999900099"],
        }
    )

    processor = SameEmitterRecipientTableProcessor(
        bs_data_dfs={BSDD: bsdd_df},
        transporters_data_dfs={BSDD: bsdd_transport_df},
        data_date_interval=data_date_interval,
    )

    assert processor.build() == {}


