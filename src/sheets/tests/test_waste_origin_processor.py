from datetime import datetime
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from ..graph_processors.plotly_components import WasteOriginProcessor

tz = ZoneInfo("Europe/Paris")

COMPANY_SIRET = "43210987654321"


@pytest.fixture
def departements_regions_df():
    return pl.LazyFrame(
        {
            "DEP": ["75", "13", "69", "33"],
            "LIBELLE": ["Paris", "Bouches-du-Rhone", "Rhone", "Gironde"],
            "REG": ["11", "93", "84", "75"],
        }
    )


@pytest.fixture
def departements_regions_df_extended():
    return pl.LazyFrame(
        {
            "DEP": ["75", "13", "33", "74", "2A", "2B", "971", "972"],
            "LIBELLE": [
                "Paris",
                "Bouches-du-Rhone",
                "Gironde",
                "Haute-Savoie",
                "Corse-du-Sud",
                "Haute-Corse",
                "Guadeloupe",
                "Martinique",
            ],
            "REG": ["11", "93", "75", "84", "94", "94", "01", "02"],
        }
    )


@pytest.fixture
def data_date_interval():
    return (
        datetime(2024, 1, 1, tzinfo=tz),
        datetime(2024, 12, 31, tzinfo=tz),
    )


@pytest.fixture
def bsdd_data():
    return pl.LazyFrame(
        {
            "id": ["bsdd-1", "bsdd-2"],
            "emitter_company_siret": ["11111111111111", "22222222222222"],
            "emitter_company_address": [
                "10 Rue Bordeaux, 33000 Bordeaux",
                "20 Rue Paris, 75002 Paris",
            ],
            "recipient_company_siret": [COMPANY_SIRET, COMPANY_SIRET],
            "received_at": [
                datetime(2024, 1, 15, tzinfo=tz),
                datetime(2024, 2, 20, tzinfo=tz),
            ],
            "quantity_received": [25.0, 35.0],
            "waste_code": ["01 01 01", "01 01 02"],
        }
    )


@pytest.fixture
def bsda_data():
    return pl.LazyFrame(
        {
            "id": ["bsda-1", "bsda-2"],
            "emitter_company_siret": ["11111111111111", "22222222222222"],
            "emitter_company_address": [
                "10 Rue Bordeaux, 33000 Bordeaux",
                "20 Rue Paris, 75002 Paris",
            ],
            "recipient_company_siret": [COMPANY_SIRET, COMPANY_SIRET],
            "received_at": [
                datetime(2024, 3, 10, tzinfo=tz),
                datetime(2024, 4, 5, tzinfo=tz),
            ],
            "quantity_received": [10.0, 20.0],
            "waste_code": ["17 06 05*", "17 06 05*"],
        }
    )


@pytest.fixture
def registry_data():
    return pl.LazyFrame(
        {
            "id": ["reg-1", "reg-2"],
            "siret": [COMPANY_SIRET, COMPANY_SIRET],
            "postal_code": ["75010", "33000"],
            "weight_value": [10.0, 20.0],
            "reception_date": [
                datetime(2024, 1, 10, tzinfo=tz),
                datetime(2024, 3, 5, tzinfo=tz),
            ],
        }
    )


# ── BSDD ──────────────────────────────────────────────────────────────────────


def test_bsdd_quantities_aggregated_correctly(bsdd_data, departements_regions_df, data_date_interval):
    """GIVEN BSDD data with two bordereaux (25.0 + 35.0)
    WHEN _preprocess_data is called with waste_type="bsdd"
    THEN total quantity = 60.0
    """
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="bsdd",
        data_df=bsdd_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert processor.preprocessed_serie["quantity_received"].sum() == pytest.approx(60.0)


def test_bsdd_departments_extracted_from_address(bsdd_data, departements_regions_df, data_date_interval):
    """GIVEN BSDD data with addresses containing postal codes 33000 and 75002
    WHEN _preprocess_data is called with waste_type="bsdd"
    THEN cp_formatted contains "Gironde (33)" and "Paris (75)"
    """
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="bsdd",
        data_df=bsdd_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    cp_values = processor.preprocessed_serie["cp_formatted"].to_list()
    assert "Gironde (33)" in cp_values
    assert "Paris (75)" in cp_values


def test_bsdd_quantity_refused_subtracted(departements_regions_df, data_date_interval):
    """GIVEN BSDD data with quantity_refused = 5.0 and quantity_received = 25.0
    WHEN _preprocess_data is called with waste_type="bsdd"
    THEN effective quantity = 20.0
    """
    data = pl.LazyFrame(
        {
            "id": ["bsdd-1"],
            "emitter_company_siret": ["11111111111111"],
            "emitter_company_address": ["10 Rue Bordeaux, 33000 Bordeaux"],
            "recipient_company_siret": [COMPANY_SIRET],
            "received_at": [datetime(2024, 1, 15, tzinfo=tz)],
            "quantity_received": [25.0],
            "quantity_refused": [5.0],
            "waste_code": ["01 01 01"],
        }
    )
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="bsdd",
        data_df=data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert processor.preprocessed_serie["quantity_received"].sum() == pytest.approx(20.0)


def test_bsdd_cedex_address_extracts_postal_code_not_cedex_code(
    departements_regions_df_extended, data_date_interval
):
    """GIVEN a BSDD address containing a CEDEX service code before the postal code
       (e.g. '2 RUE MARC LE ROUX CS 97006 74000 ANNECY')
    WHEN _preprocess_data is called with waste_type="bsdd"
    THEN the department is extracted from the postal code (74) not the CEDEX code (97006)
    """
    data = pl.LazyFrame(
        {
            "id": ["bsdd-1"],
            "emitter_company_siret": ["11111111111111"],
            "emitter_company_address": ["2 RUE MARC LE ROUX CS 97006 74000 ANNECY"],
            "recipient_company_siret": [COMPANY_SIRET],
            "received_at": [datetime(2024, 1, 15, tzinfo=tz)],
            "quantity_received": [10.0],
            "waste_code": ["01 01 01"],
        }
    )
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="bsdd",
        data_df=data,
        departements_regions_df=departements_regions_df_extended,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    cp_values = processor.preprocessed_serie["cp_formatted"].to_list()
    assert "Haute-Savoie (74)" in cp_values
    assert all("97" not in v for v in cp_values)


# ── BSDA ──────────────────────────────────────────────────────────────────────


def test_bsda_quantities_aggregated_correctly(bsda_data, departements_regions_df, data_date_interval):
    """GIVEN BSDA data with two bordereaux (10.0 + 20.0)
    WHEN _preprocess_data is called with waste_type="bsda"
    THEN total quantity = 30.0
    """
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="bsda",
        data_df=bsda_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert processor.preprocessed_serie["quantity_received"].sum() == pytest.approx(30.0)


def test_bsda_departments_extracted_from_address(bsda_data, departements_regions_df, data_date_interval):
    """GIVEN BSDA data with addresses containing postal codes 33000 and 75002
    WHEN _preprocess_data is called with waste_type="bsda"
    THEN cp_formatted contains "Gironde (33)" and "Paris (75)"
    """
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="bsda",
        data_df=bsda_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    cp_values = processor.preprocessed_serie["cp_formatted"].to_list()
    assert "Gironde (33)" in cp_values
    assert "Paris (75)" in cp_values


def test_bsda_quantity_refused_subtracted(departements_regions_df, data_date_interval):
    """GIVEN BSDA data with quantity_refused = 3.0 and quantity_received = 10.0
    WHEN _preprocess_data is called with waste_type="bsda"
    THEN effective quantity = 7.0
    """
    data = pl.LazyFrame(
        {
            "id": ["bsda-1"],
            "emitter_company_siret": ["11111111111111"],
            "emitter_company_address": ["10 Rue Bordeaux, 33000 Bordeaux"],
            "recipient_company_siret": [COMPANY_SIRET],
            "received_at": [datetime(2024, 1, 15, tzinfo=tz)],
            "quantity_received": [10.0],
            "quantity_refused": [3.0],
            "waste_code": ["17 06 05*"],
        }
    )
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="bsda",
        data_df=data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert processor.preprocessed_serie["quantity_received"].sum() == pytest.approx(7.0)


# ── TEXS ──────────────────────────────────────────────────────────────────────


def test_texs_quantities_aggregated_correctly(registry_data, departements_regions_df, data_date_interval):
    """GIVEN TEXS registry data with postal codes and weights (10.0 + 20.0)
    WHEN _preprocess_data is called with waste_type="texs"
    THEN total quantity = 30.0
    """
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="texs",
        data_df=registry_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert processor.preprocessed_serie["quantity_received"].sum() == pytest.approx(30.0)


def test_texs_departments_mapped_from_postal_code(registry_data, departements_regions_df, data_date_interval):
    """GIVEN TEXS registry data with postal codes 75010 and 33000
    WHEN _preprocess_data is called with waste_type="texs"
    THEN cp_formatted contains "Paris (75)" and "Gironde (33)"
    """
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="texs",
        data_df=registry_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    cp_values = processor.preprocessed_serie["cp_formatted"].to_list()
    assert "Paris (75)" in cp_values
    assert "Gironde (33)" in cp_values


# ── DND ───────────────────────────────────────────────────────────────────────


def test_dnd_quantities_aggregated_correctly(registry_data, departements_regions_df, data_date_interval):
    """GIVEN DND registry data with postal codes and weights (10.0 + 20.0)
    WHEN _preprocess_data is called with waste_type="dnd"
    THEN total quantity = 30.0
    """
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="dnd",
        data_df=registry_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert processor.preprocessed_serie["quantity_received"].sum() == pytest.approx(30.0)


def test_dnd_departments_mapped_from_postal_code(registry_data, departements_regions_df, data_date_interval):
    """GIVEN DND registry data with postal codes 75010 and 33000
    WHEN _preprocess_data is called with waste_type="dnd"
    THEN cp_formatted contains "Paris (75)" and "Gironde (33)"
    """
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="dnd",
        data_df=registry_data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    cp_values = processor.preprocessed_serie["cp_formatted"].to_list()
    assert "Paris (75)" in cp_values
    assert "Gironde (33)" in cp_values


# ── Top-10 ────────────────────────────────────────────────────────────────────


def test_top_10_departments_kept_others_grouped(data_date_interval):
    """GIVEN BSDD data with 12 different departments
    WHEN _preprocess_data is called
    THEN only 10 departments kept individually, rest grouped as "Autres origines" → 11 entries total
    """
    departements_df = pl.LazyFrame(
        {
            "DEP": [f"{i:02d}" for i in range(1, 13)],
            "LIBELLE": [f"Dep{i}" for i in range(1, 13)],
            "REG": ["01"] * 12,
        }
    )
    addresses = [f"1 Rue, {i:02d}000 Ville" for i in range(1, 13)]
    quantities = [float(i * 10) for i in range(1, 13)]

    data = pl.LazyFrame(
        {
            "id": [f"bsdd-{i}" for i in range(1, 13)],
            "emitter_company_siret": ["11111111111111"] * 12,
            "emitter_company_address": addresses,
            "recipient_company_siret": [COMPANY_SIRET] * 12,
            "received_at": [datetime(2024, 1, 15, tzinfo=tz)] * 12,
            "quantity_received": quantities,
            "waste_code": ["01 01 01"] * 12,
        }
    )

    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="bsdd",
        data_df=data,
        departements_regions_df=departements_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    departments = processor.preprocessed_serie["cp_formatted"].to_list()
    assert "Autres origines" in departments
    assert len(departments) == 11


# ── Special postal codes ───────────────────────────────────────────────────────


def test_corse_postal_codes_split_into_2a_2b(departements_regions_df_extended, data_date_interval):
    """GIVEN registry data with postal codes 20100 (2A) and 20200 (2B)
    WHEN _preprocess_data is called with waste_type="texs"
    THEN cp_formatted contains "Corse-du-Sud (2A)" and "Haute-Corse (2B)"
    """
    data = pl.LazyFrame(
        {
            "id": ["reg-1", "reg-2"],
            "siret": [COMPANY_SIRET, COMPANY_SIRET],
            "postal_code": ["20100", "20200"],
            "weight_value": [10.0, 15.0],
            "reception_date": [datetime(2024, 1, 10, tzinfo=tz)] * 2,
        }
    )
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="texs",
        data_df=data,
        departements_regions_df=departements_regions_df_extended,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    cp_values = processor.preprocessed_serie["cp_formatted"].to_list()
    assert "Corse-du-Sud (2A)" in cp_values
    assert "Haute-Corse (2B)" in cp_values


def test_drom_com_postal_codes_use_3_digits(departements_regions_df_extended, data_date_interval):
    """GIVEN registry data with postal code 97100 (Guadeloupe)
    WHEN _preprocess_data is called with waste_type="dnd"
    THEN cp_formatted contains "Guadeloupe (971)"
    """
    data = pl.LazyFrame(
        {
            "id": ["reg-1"],
            "siret": [COMPANY_SIRET],
            "postal_code": ["97100"],
            "weight_value": [10.0],
            "reception_date": [datetime(2024, 1, 10, tzinfo=tz)],
        }
    )
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="dnd",
        data_df=data,
        departements_regions_df=departements_regions_df_extended,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert "Guadeloupe (971)" in processor.preprocessed_serie["cp_formatted"].to_list()


# ── Edge cases ────────────────────────────────────────────────────────────────


def test_data_df_none_returns_empty_figure(departements_regions_df, data_date_interval):
    """GIVEN data_df=None
    WHEN build() is called
    THEN returns "{}" without raising
    """
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="bsdd",
        data_df=None,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert result == {}


def test_empty_postal_code_mapped_to_origine_inconnue(departements_regions_df, data_date_interval):
    """GIVEN registry data with empty postal_code strings
    WHEN _preprocess_data is called
    THEN those rows appear under "Origine inconnue"
    """
    data = pl.LazyFrame(
        {
            "id": ["reg-1", "reg-2"],
            "siret": [COMPANY_SIRET, COMPANY_SIRET],
            "postal_code": ["", ""],
            "weight_value": [5.0, 8.0],
            "reception_date": [
                datetime(2024, 1, 10, tzinfo=tz),
                datetime(2024, 2, 5, tzinfo=tz),
            ],
        }
    )
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="texs",
        data_df=data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is not None
    assert "Origine inconnue" in processor.preprocessed_serie["cp_formatted"].to_list()
    unknown_qty = processor.preprocessed_serie.filter(pl.col("cp_formatted") == "Origine inconnue")[
        "quantity_received"
    ][0]
    assert unknown_qty == pytest.approx(13.0)


def test_date_outside_interval_filtered_out(departements_regions_df, data_date_interval):
    """GIVEN registry data where all dates are outside the date interval
    WHEN _preprocess_data is called
    THEN preprocessed_serie is None (no data passes the filter)
    """
    data = pl.LazyFrame(
        {
            "id": ["reg-1"],
            "siret": [COMPANY_SIRET],
            "postal_code": ["75010"],
            "weight_value": [10.0],
            "reception_date": [datetime(2023, 6, 1, tzinfo=tz)],  # before interval
        }
    )
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="texs",
        data_df=data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    processor._preprocess_data()

    assert processor.preprocessed_serie is None


def test_all_quantities_zero_returns_empty_figure(departements_regions_df, data_date_interval):
    """GIVEN registry data where all weight_value are 0
    WHEN build() is called
    THEN returns "{}" so the no-data placeholder is shown instead of an empty chart
    """
    data = pl.LazyFrame(
        {
            "id": ["reg-1"],
            "siret": [COMPANY_SIRET],
            "postal_code": ["75010"],
            "weight_value": [0.0],
            "reception_date": [datetime(2024, 1, 10, tzinfo=tz)],
        }
    )
    processor = WasteOriginProcessor(
        company_siret=COMPANY_SIRET,
        waste_type="dnd",
        data_df=data,
        departements_regions_df=departements_regions_df,
        data_date_interval=data_date_interval,
    )
    result = processor.build()

    assert result == {}
