import csv
import io
from operator import itemgetter
from urllib.parse import urlencode

import pandas as pd
import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse

from maps.factories import CartoCompanyFactory

from ..constants import BSDA, BSDASRI, BSDD, BSDND, BSFF, BSVHU, DND, SSD, TEXS, TEXS_DD

pytestmark = pytest.mark.django_db


def test_map_api_objects_deny_anon(api_anon):
    url = reverse("map_api_objects")
    res = api_anon.get(url)
    assert res.status_code == 403


def test_map_api_objects_deny_not_verified(logged_in_api):
    url = reverse("map_api_objects")
    res = logged_in_api.get(url)
    assert res.status_code == 403


def test_map_api_region_companies(verified_api):
    CartoCompanyFactory(code_region_insee="93", coords=Point(x=5.50, y=44.22))
    CartoCompanyFactory(code_region_insee="93", coords=Point(x=5.50, y=44.22))
    CartoCompanyFactory(code_region_insee="84", coords=Point(x=5.50, y=44.22))
    url = reverse("map_api_objects")
    res = verified_api.get(f"{url}?bounds=-5.14,42.332,8.2302,51.089")  # bounds have no filtering effect
    assert res.status_code == 200
    data = res.json()

    assert data["companies"] == []
    assert data["total_count"] == 3

    assert sorted(data["clusters"], key=itemgetter("name")) == sorted(
        [
            {"name": "Provence-Alpes-Côte d'Azur", "lat": 43.955000000000005, "long": 6.053333333333333, "count": 2},
            {"name": "Auvergne Rhône-Alpes", "lat": 45.51583333333333, "long": 4.538055555555555, "count": 1},
        ],
        key=itemgetter("name"),
    )


def test_map_api_department_companies(verified_api):
    CartoCompanyFactory(code_departement_insee="83", coords=Point(x=5.50, y=43.22))
    CartoCompanyFactory(code_departement_insee="83", coords=Point(x=5.50, y=43.22))
    CartoCompanyFactory(code_departement_insee="13", coords=Point(x=5.50, y=43.22))
    url = reverse("map_api_objects")

    res = verified_api.get(
        f"{url}?bounds=4.666261723488475%2C42.96291945615462%2C7.741025145703958%2C44.28842293075769"
    )
    assert res.status_code == 200
    data = res.json()

    assert data["companies"] == []
    assert data["total_count"] == 3

    assert sorted(data["clusters"], key=itemgetter("name")) == sorted(
        [
            {"name": "Bouches-du-Rhône", "lat": 43.54333333333333, "long": 5.086388888888888, "count": 1},
            {"name": "Var", "lat": 43.46055555555556, "long": 6.218055555555556, "count": 2},
        ],
        key=itemgetter("name"),
    )


def test_map_api_companies(verified_api):
    CartoCompanyFactory(coords=Point(x=55.30, y=-21.22))
    company = CartoCompanyFactory(coords=Point(x=55.50, y=-21.22))
    url = reverse("map_api_objects")
    res = verified_api.get(f"{url}?bounds=55.49,-21.23,55.5745,-21.191")
    assert res.status_code == 200
    data = res.json()
    assert data["clusters"] == []
    assert data["total_count"] == 2
    companies = data["companies"]
    assert len(companies) == 1
    assert companies[0]["siret"] == company.siret


def test_map_api_companies_filter_by_operation_codes(verified_api):
    c1 = CartoCompanyFactory(coords=Point(x=55.50, y=-21.22), bsda_destination=True, processing_operations_bsda=["R1"])
    CartoCompanyFactory(coords=Point(x=55.50, y=-21.22), bsda_destination=True, processing_operations_bsda=["R2"])
    c2 = CartoCompanyFactory(
        coords=Point(x=55.50, y=-21.22),
        bsda_destination=True,
        bsdasri_destination=True,
        processing_operations_bsdasri=["R1"],
    )
    CartoCompanyFactory(coords=Point(x=55.50, y=-21.22))
    url = reverse("map_api_objects")
    # filter on bsds_roles = bsda_destination+ operation code
    res = verified_api.get(f"{url}?bounds=55.49,-21.23,55.5745,-21.191&bsds_roles=bsda_destination&operation_codes=R1")
    assert res.status_code == 200
    data = res.json()
    assert data["clusters"] == []
    assert data["total_count"] == 1
    companies = data["companies"]
    assert len(companies) == 1
    assert companies[0]["siret"] == c1.siret

    # filter on bsds_roles = bsdasri_destination+ operation code
    res = verified_api.get(
        f"{url}?bounds=55.49,-21.23,55.5745,-21.191&bsds_roles=bsdasri_destination&operation_codes=R1"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["clusters"] == []
    assert data["total_count"] == 1
    companies = data["companies"]
    assert len(companies) == 1
    assert companies[0]["siret"] == c2.siret


@pytest.mark.parametrize(
    "bsd_type",
    [
        BSDD,
        BSDND,
        BSDA,
        BSDASRI,
        BSFF,
        BSVHU,
        TEXS,
        TEXS_DD,
        DND,
        SSD,
    ],
)
def test_map_api_companies_filter_bsd_type(bsd_type, verified_api):
    CartoCompanyFactory(coords=Point(x=55.50, y=-21.22))
    url = reverse("map_api_objects")

    res = verified_api.get(f"{url}?bounds=55.49,-21.23,55.5745,-21.191&bsds_roles={bsd_type}")
    assert res.status_code == 200


@pytest.mark.parametrize(
    "bsd_type",
    [
        BSDD,
        BSDND,
        BSDA,
        BSDASRI,
        BSFF,
        BSVHU,
        TEXS,
        TEXS_DD,
        DND,
        SSD,
    ],
)
def test_map_api_companies_filter_bsd_role(bsd_type, verified_api):
    CartoCompanyFactory(coords=Point(x=55.50, y=-21.22))
    url = reverse("map_api_objects")

    res = verified_api.get(f"{url}?bounds=55.49,-21.23,55.5745,-21.191&bsds_roles={bsd_type}_destination")
    assert res.status_code == 200


# http://127.0.0.1:8000/map/api/companies/objects?bsds_roles=emitter&departments=23&bounds=1.7331376756776535%2C45.94378560421595%2C1.7969849039687915%2C45.96452217010278
def test_map_api_companies_filter_bsd_rol_emitter(verified_api):
    CartoCompanyFactory(coords=Point(x=55.50, y=-21.22))
    url = reverse("map_api_objects")

    res = verified_api.get(f"{url}?bounds=55.49,-21.23,55.5745,-21.191&bsds_roles=emitter")
    assert res.status_code == 200


@pytest.fixture
def setup_export_test_data():
    company1 = CartoCompanyFactory(
        siret="12345678901234",
        nom_etablissement="Test Company 1",
        coords=Point(x=2.35, y=48.85),  # Paris coordinates
        profils=["collector", "wasteprocessor"],
        bsdd=True,
        bsdd_emitter=True,
        bsdd_destination=True,
        processing_operations_bsdd=["R1", "D10"],
        code_departement_insee="75",
    )

    company2 = CartoCompanyFactory(
        siret="98765432109876",
        nom_etablissement="Test Company 2",
        coords=Point(x=4.85, y=45.75),  # Lyon coordinates
        profils=["transporter"],
        bsda=True,
        bsda_transporter=True,
        code_departement_insee="69",
    )

    company3 = CartoCompanyFactory(
        siret="45678901234567",
        nom_etablissement="Test Company 3",
        coords=Point(x=-1.55, y=47.22),  # Nantes coordinates
        profils=["destination"],
        bsff=True,
        bsff_destination=True,
        code_departement_insee="44",
    )

    return {"company1": company1, "company2": company2, "company3": company3}


def test_map_api_export_deny_anon(api_anon):
    url = reverse("map_api_export")
    res = api_anon.get(url)
    assert res.status_code == 403

    res = api_anon.post(url, {})
    assert res.status_code == 403


def test_map_api_export_deny_not_verified(logged_in_api):
    url = reverse("map_api_export")
    res = logged_in_api.get(url)
    assert res.status_code == 403

    res = logged_in_api.post(url, {})
    assert res.status_code == 403


def test_export_access_allowed_for_verified(verified_api):
    url = reverse("map_api_export")

    res = verified_api.post(f"{url}", {})
    assert res.status_code == 200


def test_map_api_export_deny_get(verified_api):
    CartoCompanyFactory(coords=Point(x=55.30, y=-21.22), siret="00035182679548", nom_etablissement="Mycompany")
    url = reverse("map_api_export")
    params = {"export_format": "csv"}

    res = verified_api.get(f"{url}?{urlencode(params)}")

    assert res.status_code == 405


def test_map_api_export(verified_api):
    CartoCompanyFactory(coords=Point(x=55.30, y=-21.22), siret="00035182679548", nom_etablissement="Mycompany")
    url = reverse("map_api_export")
    params = {"export_format": "csv"}

    res = verified_api.post(f"{url}?{urlencode(params)}", {})

    assert res.status_code == 200
    assert (
        res.content
        == b"siret,nom_etablissement,adresse_td,profiles,bsdd_roles,bsdnd_roles,bsda_roles,bsff_roles,bsdasri_roles,bsvhu_roles,texs_dd_roles,dnd_roles,texs_roles,processing_operations\r\n00035182679548,Mycompany,,,,,,,,,,,,\r\n"
    )


def test_export_csv_format(verified_api, setup_export_test_data):
    companies = setup_export_test_data
    url = reverse("map_api_export")

    params = {"export_format": "csv", "bounds": "-5.142222,42.332778,8.230278,51.089167"}

    response = verified_api.post(f"{url}?{urlencode(params)}", {})

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert "attachment; filename=" in response["Content-Disposition"]

    # Parse CSV content
    content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)

    assert len(rows) == 3

    siret_to_row = {row["siret"]: row for row in rows}

    company1_row = siret_to_row[companies["company1"].siret]
    assert company1_row["nom_etablissement"] == companies["company1"].nom_etablissement
    assert company1_row["bsdd_roles"] == "Producteur - émetteur, Destinataire"

    assert company1_row["processing_operations"] == "D10, R1"

    company2_row = siret_to_row[companies["company2"].siret]
    assert company2_row["nom_etablissement"] == companies["company2"].nom_etablissement

    assert company2_row["bsda_roles"] == "Transporteur"

    company3_row = siret_to_row[companies["company3"].siret]
    assert company3_row["nom_etablissement"] == companies["company3"].nom_etablissement

    assert company3_row["bsff_roles"] == "Destinataire"


def test_export_xlsx_format(verified_api, setup_export_test_data):
    url = reverse("map_api_export")

    params = {"export_format": "xlsx", "bounds": "-5.142222,42.332778,8.230278,51.089167"}

    response = verified_api.post(f"{url}?{urlencode(params)}", {})

    assert response.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response["Content-Type"]
    assert "attachment; filename=" in response["Content-Disposition"]

    content = b"".join(response.streaming_content)
    df = pd.read_excel(io.BytesIO(content))

    assert len(df) == 3

    expected_columns = ["siret", "nom_etablissement", "adresse_td", "profiles"]
    for col in expected_columns:
        assert col in df.columns
    records = df.to_dict("records")
    subset = [{"siret": row["siret"], "nom_etablissement": row["nom_etablissement"]} for row in records]

    assert subset == [
        {"siret": 12345678901234, "nom_etablissement": "Test Company 1"},
        {"siret": 98765432109876, "nom_etablissement": "Test Company 2"},
        {"siret": 45678901234567, "nom_etablissement": "Test Company 3"},
    ]
