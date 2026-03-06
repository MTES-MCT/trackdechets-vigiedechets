from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from sheets.constants import BSDA, BSDD
from sheets.graph_processors.html_components.bsd_auto_approved_revision_table_processor import (
    BsdAutoApprovedRevisionTableProcessor,
)

tz = ZoneInfo("Europe/Paris")


@pytest.fixture
def data_date_interval():
    return (datetime(2024, 1, 1, tzinfo=tz), datetime(2024, 12, 31, tzinfo=tz))


def make_bsdd_revision_df(rows: list[dict]) -> pl.LazyFrame:
    schema = {
        "id": pl.String,
        "bs_id": pl.String,
        "updated_at": pl.Datetime(time_unit="us", time_zone="Europe/Paris"),
        "comment": pl.String,
        "readable_id": pl.String,
        "emitter_company_siret": pl.String,
        "emitter_is_private_individual": pl.Boolean,
        "emitter_company_omi_number": pl.String,
        "recipient_company_siret": pl.String,
        "waste_details_code": pl.String,
        "initial_waste_details_code": pl.String,
        "waste_details_name": pl.String,
        "initial_waste_details_name": pl.String,
        "quantity_received": pl.Float64,
        "initial_quantity_received": pl.Float64,
        "processing_operation_done": pl.String,
        "initial_processing_operation_done": pl.String,
        "waste_details_quantity": pl.Float64,
        "initial_waste_details_quantity": pl.Float64,
        "recipient_cap": pl.String,
        "initial_recipient_cap": pl.String,
        "destination_operation_mode": pl.String,
        "initial_destination_operation_mode": pl.String,
        "waste_acceptation_status": pl.String,
        "initial_waste_acceptation_status": pl.String,
        "quantity_refused": pl.Float64,
        "initial_quantity_refused": pl.Float64,
        "waste_refusal_reason": pl.String,
        "initial_waste_refusal_reason": pl.String,
        "waste_details_pop": pl.Boolean,
        "initial_waste_details_pop": pl.Boolean,
    }
    defaults = {
        "emitter_company_omi_number": None,
        "emitter_is_private_individual": False,
        "comment": None,
        "waste_details_code": None,
        "initial_waste_details_code": None,
        "waste_details_name": None,
        "initial_waste_details_name": None,
        "quantity_received": None,
        "initial_quantity_received": None,
        "processing_operation_done": None,
        "initial_processing_operation_done": None,
        "waste_details_quantity": None,
        "initial_waste_details_quantity": None,
        "recipient_cap": None,
        "initial_recipient_cap": None,
        "destination_operation_mode": None,
        "initial_destination_operation_mode": None,
        "waste_acceptation_status": None,
        "initial_waste_acceptation_status": None,
        "quantity_refused": None,
        "initial_quantity_refused": None,
        "waste_refusal_reason": None,
        "initial_waste_refusal_reason": None,
        "waste_details_pop": None,
        "initial_waste_details_pop": None,
    }
    full_rows = [{**defaults, **row} for row in rows]
    return pl.DataFrame(full_rows, schema_overrides=schema).lazy()


def make_bsda_revision_df(rows: list[dict]) -> pl.LazyFrame:
    schema = {
        "id": pl.String,
        "bs_id": pl.String,
        "updated_at": pl.Datetime(time_unit="us", time_zone="Europe/Paris"),
        "comment": pl.String,
        "readable_id": pl.String,
        "emitter_company_siret": pl.String,
        "emitter_is_private_individual": pl.Boolean,
        "recipient_company_siret": pl.String,
        "waste_code": pl.String,
        "initial_waste_code": pl.String,
        "waste_material_name": pl.String,
        "initial_waste_material_name": pl.String,
        "destination_reception_weight": pl.Float64,
        "initial_destination_reception_weight": pl.Float64,
        "destination_operation_code": pl.String,
        "initial_destination_operation_code": pl.String,
        "destination_cap": pl.String,
        "initial_destination_cap": pl.String,
        "destination_operation_mode": pl.String,
        "initial_destination_operation_mode": pl.String,
        "waste_pop": pl.Boolean,
        "initial_waste_pop": pl.Boolean,
    }
    defaults = {
        "emitter_is_private_individual": True,
        "comment": None,
        "waste_code": None,
        "initial_waste_code": None,
        "waste_material_name": None,
        "initial_waste_material_name": None,
        "destination_reception_weight": None,
        "initial_destination_reception_weight": None,
        "destination_operation_code": None,
        "initial_destination_operation_code": None,
        "destination_cap": None,
        "initial_destination_cap": None,
        "destination_operation_mode": None,
        "initial_destination_operation_mode": None,
        "waste_pop": None,
        "initial_waste_pop": None,
    }
    full_rows = [{**defaults, **row} for row in rows]
    return pl.DataFrame(full_rows, schema_overrides=schema).lazy()


def test_bsdd_single_changed_field(data_date_interval):
    """GIVEN a BSDD auto-approved revision with one changed field
    WHEN building the table
    THEN it returns one row with the correct field label, previous and new values.
    """
    df = make_bsdd_revision_df(
        [
            {
                "id": "rev-1",
                "bs_id": "bsdd-1",
                "readable_id": "BSD-20240101-AAAA",
                "updated_at": datetime(2024, 3, 15, 10, 0, tzinfo=tz),
                "comment": "Correction code déchet",
                "emitter_company_siret": None,
                "emitter_is_private_individual": True,
                "recipient_company_siret": "12345678900011",
                "waste_details_code": "20 01 27*",
                "initial_waste_details_code": "20 01 01",
            }
        ]
    )

    processor = BsdAutoApprovedRevisionTableProcessor(
        company_siret="12345678900011",
        auto_approved_revision_dfs={BSDD: df},
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert len(result) == 1
    row = result[0]
    assert row["readable_id"] == "BSD-20240101-AAAA"
    assert row["updated_at"] == "15/03/2024 10:00"
    assert row["emitter_company_siret"] == "N/A (particulier)"
    assert row["recipient_company_siret"] == "12345678900011"
    assert row["comment"] == "Correction code déchet"
    assert row["field_name"] == "Code déchet"
    assert row["previous_value"] == "20 01 01"
    assert row["new_value"] == "20 01 27*"


def test_bsdd_multiple_changed_fields_produces_multiple_rows(data_date_interval):
    """GIVEN a BSDD revision where two fields changed
    WHEN building the table
    THEN it returns one row per changed field.
    """
    df = make_bsdd_revision_df(
        [
            {
                "id": "rev-2",
                "bs_id": "bsdd-2",
                "readable_id": "BSD-20240201-BBBB",
                "updated_at": datetime(2024, 4, 10, 9, 30, tzinfo=tz),
                "emitter_company_siret": None,
                "emitter_is_private_individual": True,
                "recipient_company_siret": "12345678900011",
                "waste_details_code": "20 01 27*",
                "initial_waste_details_code": "20 01 01",
                "quantity_received": 15.5,
                "initial_quantity_received": 20.0,
            }
        ]
    )

    processor = BsdAutoApprovedRevisionTableProcessor(
        company_siret="12345678900011",
        auto_approved_revision_dfs={BSDD: df},
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert len(result) == 2
    field_names = {row["field_name"] for row in result}
    assert "Code déchet" in field_names
    assert "Quantité reçue (t)" in field_names


def test_bsdd_omi_ship_emitter_label(data_date_interval):
    """GIVEN a BSDD revision where the emitter is an OMI ship
    WHEN building the table
    THEN the emitter SIRET is labeled 'N/I (navire OMI)'.
    """
    df = make_bsdd_revision_df(
        [
            {
                "id": "rev-3",
                "bs_id": "bsdd-3",
                "readable_id": "BSD-20240301-CCCC",
                "updated_at": datetime(2024, 5, 1, 14, 0, tzinfo=tz),
                "emitter_company_siret": None,
                "emitter_is_private_individual": False,
                "emitter_company_omi_number": "IMO1234567",
                "recipient_company_siret": "12345678900011",
                "waste_details_name": "Huiles usagées",
                "initial_waste_details_name": "Huiles",
            }
        ]
    )

    processor = BsdAutoApprovedRevisionTableProcessor(
        company_siret="12345678900011",
        auto_approved_revision_dfs={BSDD: df},
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert len(result) == 1
    assert result[0]["emitter_company_siret"] == "N/I (navire OMI)"


def test_bsdd_company_emitter_keeps_siret(data_date_interval):
    """GIVEN a BSDD revision where the emitter is a company
    WHEN building the table
    THEN the emitter SIRET is kept as-is.
    """
    df = make_bsdd_revision_df(
        [
            {
                "id": "rev-4",
                "bs_id": "bsdd-4",
                "readable_id": "bsdd-4",
                "updated_at": datetime(2024, 6, 1, 8, 0, tzinfo=tz),
                "emitter_company_siret": "98765432100022",
                "emitter_is_private_individual": False,
                "emitter_company_omi_number": None,
                "recipient_company_siret": "12345678900011",
                "waste_details_code": "20 01 28",
                "initial_waste_details_code": "20 01 27*",
            }
        ]
    )

    processor = BsdAutoApprovedRevisionTableProcessor(
        company_siret="12345678900011",
        auto_approved_revision_dfs={BSDD: df},
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert len(result) == 1
    assert result[0]["emitter_company_siret"] == "98765432100022"


def test_revision_outside_date_interval_is_excluded(data_date_interval):
    """GIVEN a revision with updated_at outside the date interval
    WHEN building the table
    THEN it returns no rows.
    """
    df = make_bsdd_revision_df(
        [
            {
                "id": "rev-5",
                "bs_id": "bsdd-5",
                "readable_id": "bsdd-5",
                "updated_at": datetime(2023, 6, 1, 8, 0, tzinfo=tz),  # before interval
                "emitter_company_siret": None,
                "emitter_is_private_individual": True,
                "recipient_company_siret": "12345678900011",
                "waste_details_code": "20 01 27*",
                "initial_waste_details_code": "20 01 01",
            }
        ]
    )

    processor = BsdAutoApprovedRevisionTableProcessor(
        company_siret="12345678900011",
        auto_approved_revision_dfs={BSDD: df},
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert result == []


def test_unchanged_fields_produce_no_rows(data_date_interval):
    """GIVEN a revision where initial and current values are identical
    WHEN building the table
    THEN it returns no rows for those fields.
    """
    df = make_bsdd_revision_df(
        [
            {
                "id": "rev-6",
                "bs_id": "bsdd-6",
                "readable_id": "bsdd-6",
                "updated_at": datetime(2024, 7, 1, 8, 0, tzinfo=tz),
                "emitter_company_siret": None,
                "emitter_is_private_individual": True,
                "recipient_company_siret": "12345678900011",
                "waste_details_code": "20 01 01",
                "initial_waste_details_code": "20 01 01",  # same value
            }
        ]
    )

    processor = BsdAutoApprovedRevisionTableProcessor(
        company_siret="12345678900011",
        auto_approved_revision_dfs={BSDD: df},
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert result == []


def test_both_null_fields_produce_no_rows(data_date_interval):
    """GIVEN a revision where both initial and current values are None
    WHEN building the table
    THEN it returns no rows for those fields.
    """
    df = make_bsdd_revision_df(
        [
            {
                "id": "rev-7",
                "bs_id": "bsdd-7",
                "readable_id": "bsdd-7",
                "updated_at": datetime(2024, 8, 1, 8, 0, tzinfo=tz),
                "emitter_company_siret": None,
                "emitter_is_private_individual": True,
                "recipient_company_siret": "12345678900011",
                # all field pairs remain None (defaults)
            }
        ]
    )

    processor = BsdAutoApprovedRevisionTableProcessor(
        company_siret="12345678900011",
        auto_approved_revision_dfs={BSDD: df},
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert result == []


def test_empty_input_returns_empty_list(data_date_interval):
    """GIVEN no auto-approved revision data
    WHEN building the table
    THEN it returns an empty list.
    """
    processor = BsdAutoApprovedRevisionTableProcessor(
        company_siret="12345678900011",
        auto_approved_revision_dfs={},
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert result == []


def test_bsda_revision(data_date_interval):
    """GIVEN a BSDA auto-approved revision (private individual emitter, no work company)
    WHEN building the table
    THEN it returns the correct rows with BSDA field labels.
    """
    df = make_bsda_revision_df(
        [
            {
                "id": "rev-8",
                "bs_id": "bsda-1",
                "readable_id": "BSDA-20240101-XXXX",
                "updated_at": datetime(2024, 2, 20, 11, 0, tzinfo=tz),
                "comment": "Correction poids",
                "emitter_company_siret": None,
                "emitter_is_private_individual": True,
                "recipient_company_siret": "12345678900011",
                "destination_reception_weight": 5.0,
                "initial_destination_reception_weight": 3.5,
            }
        ]
    )

    processor = BsdAutoApprovedRevisionTableProcessor(
        company_siret="12345678900011",
        auto_approved_revision_dfs={BSDA: df},
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert len(result) == 1
    row = result[0]
    assert row["readable_id"] == "BSDA-20240101-XXXX"
    assert row["updated_at"] == "20/02/2024 11:00"
    assert row["emitter_company_siret"] == "N/A (particulier)"
    assert row["field_name"] == "Quantité reçue (t)"
    assert row["previous_value"] == "3.5"
    assert row["new_value"] == "5.0"


def test_mixed_bsdd_and_bsda(data_date_interval):
    """GIVEN auto-approved revisions for both BSDD and BSDA
    WHEN building the table
    THEN it returns rows from both types combined and sorted by date.
    """
    bsdd_df = make_bsdd_revision_df(
        [
            {
                "id": "rev-bsdd",
                "bs_id": "bsdd-10",
                "readable_id": "bsdd-10",
                "updated_at": datetime(2024, 6, 1, 10, 0, tzinfo=tz),
                "emitter_company_siret": None,
                "emitter_is_private_individual": True,
                "recipient_company_siret": "12345678900011",
                "waste_details_code": "20 01 27*",
                "initial_waste_details_code": "20 01 01",
            }
        ]
    )
    bsda_df = make_bsda_revision_df(
        [
            {
                "id": "rev-bsda",
                "bs_id": "bsda-10",
                "readable_id": "bsda-10",
                "updated_at": datetime(2024, 3, 1, 8, 0, tzinfo=tz),
                "emitter_company_siret": None,
                "emitter_is_private_individual": True,
                "recipient_company_siret": "12345678900011",
                "waste_code": "17 06 05*",
                "initial_waste_code": "17 06 01*",
            }
        ]
    )

    processor = BsdAutoApprovedRevisionTableProcessor(
        company_siret="12345678900011",
        auto_approved_revision_dfs={BSDD: bsdd_df, BSDA: bsda_df},
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert len(result) == 2
    # sorted by updated_at: BSDA (March) before BSDD (June)
    assert result[0]["id"] == "bsda-10"
    assert result[1]["id"] == "bsdd-10"
