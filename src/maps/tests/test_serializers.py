import pytest

from ..factories import CartoCompanyFactory
from ..serializers import CompanySerializer

pytestmark = pytest.mark.django_db


def test_company_serializer():
    company = CartoCompanyFactory(
        bsdd=True,
        bsda=True,
        bsff=True,
        bsdasri=True,
        bsvhu=True,
        profils=[
            "COLLECTOR",
            "WASTEPROCESSOR",
            "WASTE_CENTER",
            "BROKER",
            "TRADER",
            "TRANSPORTER",
            "ECO_ORGANISM",
            "ECO_ORGANISME",
            "PRODUCER",
            "WASTE_VEHICLES",
            "CREMATORIUM",
            "WORKER",
        ],
        is_dormant=False,
    )
    ser = CompanySerializer(company)
    serialized_profiles = [
        "Tri Transit Regroupement (TTR)",
        "Usine de traitement",
        "Déchetterie",
        "Courtier",
        "Négociant",
        "Transporteur",
        "Éco-organisme",
        "Éco-organisme",
        "Producteur",
        "Centre Véhicules Hors d'Usage",
        "Crématorium",
        "Entreprise de travaux",
    ]

    assert ser.data == {
        "siret": company.siret,
        "nom_etablissement": company.nom_etablissement,
        "adresse_td": company.adresse_td,
        "lat": company.coords.y,
        "long": company.coords.x,
        "wastes": "Déchets dangereux, Amiante, Fluides Frigorigènes, Dasri, Vehicules hors d'usage",
        "profiles": ", ".join(serialized_profiles),
        "registered_on_td": True,
        "is_dormant": False,
    }
