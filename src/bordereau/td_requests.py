from string import Template

import httpx
from django.conf import settings

from roadcontrol.constants import TYPE_BSDA, TYPE_BSDASRI, TYPE_BSDD, TYPE_BSFF, TYPE_BSPAOH, TYPE_BSVHU

def query_td_search_bsds(siret=None, bsd_id=None, code_postal=None, code_dechet=None, code_aiot=None, start_date_rep=None, end_date_rep=None, start_date_exp=None, end_date_exp=None, start_cursor=None, end_cursor=None):
    """
    Requete de recherche de BSDs dans Trackdéchets en fonction de différents critères (SIRET, code postal, numéro de bordereau, code déchet, code aiot et plages de dates). Seuls les critères SIRET et numéro de bordereau sont actuellement pris en compte dans la requête GraphQL, les autres critères sont ignorés pour l'instant car non supportés par l'API Trackdéchets.
    """
    where_clauses = []

    if siret:
        where_clauses.append(f'siret: "{siret}"')
    if bsd_id:
        where_clauses.append(f'readableId: "{bsd_id}"')

    # Les autres filtres ne sont pas supportés par ControlBsdWhere
    # code_postal, code_dechet, code_aiot, dates -> ignorés pour l'instant

    where = "\n".join(where_clauses)
    after = f'after: "{end_cursor}"' if end_cursor else ""

    query = graphql_query_control_bsds.substitute(
        where=where,
        after=after,
        bsdd_fragment=bsdd_fragment,
        bsdasri_fragment=bsdasri_fragment,
        bsda_fragment=bsda_fragment,
        bsvhu_fragment=bsvhu_fragment,
        bspaoh_fragment=bspaoh_fragment,
        bsff_fragment=bsff_fragment,
    )

    client = httpx.Client(timeout=60)
    try:
        res = client.post(
            url=settings.TD_API_URL,
            headers={"Authorization": f"Bearer {settings.TD_API_TOKEN}"},
            json={"query": query},
        )
        res.raise_for_status()
        return res.json()
    except (httpx.HTTPError, ValueError):
        return None

def query_td_search_companies(clue):
    """
    Requête de recherche d'entreprises dans Trackdéchets en fonction d'une "clue" qui peut être un numéro de SIRET, un numéro de TVA,
    une raison sociale ou une partie de raison sociale. La requête retourne une liste d'entreprises correspondant à la clue,
    avec leurs informations publiques (SIRET, numéro de TVA, nom, adresse, etc.).
    """
    query = """
    query SearchCompanies($clue: String!) {
      searchCompanies(clue: $clue, allowForeignCompanies: true) {
        siret
        vatNumber
        name
        address
        isRegistered
        codePaysEtrangerEtablissement
        etatAdministratif
      }
    }
    """
    payload = {"query": query, "variables": {"clue": clue}}
    client = httpx.Client(timeout=30)


    def _extract_companies(response):
      data = response.json()
      if not isinstance(data, dict):
        return None
      if data.get("errors"):
        return None
      return data.get("data", {}).get("searchCompanies", [])

    auth_headers = {"Authorization": f"Bearer {settings.TD_API_TOKEN}"}

    try:
      res = client.post(url=settings.TD_API_URL, headers=auth_headers, json=payload)
      res.raise_for_status()
      companies = _extract_companies(res)
      if companies is not None:
        return companies
    except (httpx.HTTPError, ValueError):
      pass
      
    return []


def query_td_company_infos(siret):
    """
    Requête d'information d'une entreprise dans Trackdéchets en fonction de son numéro de SIRET.
    La requête retourne les informations publiques de l'entreprise (SIRET, numéro de TVA, nom, adresse, etc.) ainsi que son statut d'inscription sur Trackdéchets.
    """
    query = """
    query GetCompanyInfos($siret: String!) {
      companyInfos(siret: $siret) {
        siret
        vatNumber
        name
        address
        isRegistered
        codePaysEtrangerEtablissement
        etatAdministratif
      }
    }
    """

    client = httpx.Client(timeout=60)
    try:
        res = client.post(
            url=settings.TD_API_URL,
            json={
                "query": query,
                "variables": {"siret": siret},
            },
        )
        res.raise_for_status()
        rep = res.json()
        data = rep.get("data", {})
        if data and "companyInfos" in data:
            return data["companyInfos"]
        return None
    except (httpx.HTTPError, ValueError):
        return None

bsdd_forms_fragment = """
fragment BsddFragment on Form {
  __typename
  id
  readableId
  customId
  status
  createdAt
  updatedAt
  emittedAt
  takenOverAt
  receivedAt
  processedAt
  wasteAcceptationStatus
  wasteRefusalReason
  quantityReceived
  processingOperationDone
  processingOperationDescription
  noTraceability
  emitter {
    company { siret name address contact phone mail }
  }
  recipient {
    company { siret name address contact phone mail }
  }
  transporter {
    company { siret name }
    numberPlate
  }
  wasteDetails {
    code
    name
    quantity
    quantityType
  }
  trader {
    company { siret name }
  }
  broker {
    company { siret name }
  }
  intermediaries {
    siret
    name
    address
    contact
    phone
    mail
  }
}
"""

graphql_query_forms = Template("""
$bsdd_fragment

query Forms(
  $$siret: String
  $$cursorAfter: ID
  $$first: Int
  $$status: [FormStatus!]
  $$roles: [FormRole!]
  $$updatedAfter: String
  $$sentAfter: String
  $$wasteCode: String
  $$customId: String
) {
  forms(
    siret: $$siret
    cursorAfter: $$cursorAfter
    first: $$first
    status: $$status
    roles: $$roles
    updatedAfter: $$updatedAfter
    sentAfter: $$sentAfter
    wasteCode: $$wasteCode
    customId: $$customId
  ) {
    ...BsddFragment
  }
}
""")


def query_td_forms(
    siret=None,
    bsd_id=None,
    start_cursor=None,
    end_cursor=None,
    status=None,
    roles=None,
    waste_code=None,
    custom_id=None,
    first=50,
    updated_after=None,
    sent_after=None,
    code_postal=None,
):
    variables = {}
    if siret:
        variables["siret"] = siret
    if end_cursor:
        variables["cursorAfter"] = end_cursor
    if custom_id:
        variables["customId"] = custom_id
    if status:
        variables["status"] = status
    if roles:
        variables["roles"] = roles
    if waste_code:
        variables["wasteCode"] = waste_code
    if first:
        variables["first"] = first
    if updated_after:
        variables["updatedAfter"] = updated_after
    if sent_after:
        variables["sentAfter"] = sent_after

    query = graphql_query_forms.substitute(bsdd_fragment=bsdd_forms_fragment)

    client = httpx.Client(timeout=60)
    try:
        res = client.post(
            url=settings.TD_API_URL,
            headers={"Authorization": f"Bearer {settings.TD_API_TOKEN}"},
            json={"query": query, "variables": variables},
        )
        rep = res.json()
    except httpx.HTTPError:
        return []

    forms = rep.get("data", {}).get("forms", []) or []

    # Filtrage par readableId côté Python si bsd_id est un BSD-XXXXXXXX
    if bsd_id:
        forms = [f for f in forms if f.get("readableId") == bsd_id]

    if not forms:
        return {
            "data": {
                "controlBsds": {
                    "totalCount": 0,
                    "pageInfo": {
                        "startCursor": None,
                        "endCursor": None,
                        "hasNextPage": False,
                        "hasPreviousPage": False,
                    },
                    "edges": [],
                }
            }
        }

    has_next_page = len(forms) == first

    return {
        "data": {
            "controlBsds": {
                "totalCount": len(forms),
                "pageInfo": {
                    "startCursor": forms[0]["id"],
                    "endCursor": forms[-1]["id"],
                    "hasNextPage": has_next_page,
                    "hasPreviousPage": end_cursor is not None,
                },
                "edges": [{"node": form} for form in forms],
            }
        }
    }