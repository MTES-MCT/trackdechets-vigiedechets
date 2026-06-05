from string import Template

import httpx
from django.conf import settings

from roadcontrol.constants import TYPE_BSDA, TYPE_BSDASRI, TYPE_BSDD, TYPE_BSFF, TYPE_BSPAOH, TYPE_BSVHU

bsdd_fragment = """
fragment BsddFragment on Form {
  __typename
  id
  readableId
  updatedAt
  bsddStatus: status
  receivedAt
  emittedAt
  wasteDetails {
    code
    name
    onuCode
    quantity
    packagingInfos {
      type
      other
      quantity
    }
  }
  stateSummary {
    quantity
  }
  emitter {
    company {
      siret
      name
      gerepId
    }
    workSite {
      name
    }
  }
  intermediaries {
    name
  }
  recipient {
    company {
      name
    }
  }
  transporters {
    company {
      siret
      name
    }
    numberPlate
  }
  transporter {
    company {
      siret
      name
    }
    numberPlate
  }
}
"""

bsdasri_fragment = """
fragment BsdasriFragment on Bsdasri {
  __typename
  id
  bsdasriUpdatedAt: updatedAt
  bsdasriStatus: status
  bsdasriWaste: waste {
    code
    adr
  }
  emitter {
    company {
      siret
      name
      gerepId
    }
  }
  transporter {
    company {
      siret
      name
    }
    transport {
      plates
      weight {
        value
      }
      packagings {
        type
        other
        quantity
        volume
      }
    }
  }
  destination {
    company {
      siret
      name
    }
    reception {
      date
    }
  }
}
"""

bsda_fragment = """
fragment BsdaFragment on Bsda {
  __typename
  id
  bsdaUpdatedAt: updatedAt
  bsdaStatus: status
  waste {
    bsdaWasteCode: code
    adr
    materialName
  }
  emitter {
    company {
      siret
      name
      gerepId
    }
  }
  transporter {
    company {
      siret
      name
    }
    transport {
      plates
    }
  }
  destination {
    company {
      siret
      name
    }
    reception {
      date
    }
  }
  bsdaPackagings: packagings {
    other
    quantity
    type
  }
  weight {
    value
  }
}
"""

bsff_fragment = """
fragment BsffFragment on Bsff {
  __typename
  id
  bsffUpdatedAt: updatedAt
  bsffStatus: status
  emitter {
    company {
      siret
      name
      gerepId
    }
  }
  bsffTransporter: transporter {
    company {
      siret
      name
    }
    transport {
      plates
    }
  }
  waste {
    code
    description
    adr
  }
  bsffDestination: destination {
    company {
      siret
      name
    }
    reception {
      date
    }
  }
  packagings {
    numero
    type
    volume
    weight
  }
  bsffWeight: weight {
    value
  }
}
"""

bsvhu_fragment = """
fragment BsvhuFragment on Bsvhu {
  __typename
  id
  wasteCode
  bsvhuStatus: status
  bsvhuUpdatedAt: updatedAt
  weight {
    value
  }
  emitter {
    company {
      siret
      name
      gerepId
    }
  }
  transporter {
    company {
      siret
      name
    }
    transport {
      plates
    }
  }
  destination {
    company {
      siret
      name
    }
    reception {
      weight
      date
    }
  }
}
"""

bspaoh_fragment = """
fragment BspaohFragment on Bspaoh {
  __typename
  id
  bspaohStatus: status
  emitter {
    company {
      siret
      name
      gerepId
    }
    emission {
      detail {
        weight {
          value
        }
      }
    }
  }
  transporter {
    company {
      siret
      name
    }
    transport {
      plates
    }
  }
  destination {
    company {
      siret
      name
    }
    reception {
      date
    }
  }
  bspaohWaste: waste {
    code
    type
    packagings {
      type
      volume
      quantity
    }
  }
}
"""

graphql_query_bordereaux_search = Template("""
 $bsdd_fragment
 $bsdasri_fragment
 $bsda_fragment
 $bsvhu_fragment
 $bspaoh_fragment
 $bsff_fragment

query BordereauxSearch {
  bordereauxSearch(
    where: {
      $where
    }
    $first
    $after
  ) {
    totalCount
    pageInfo {
      startCursor
      endCursor
      hasNextPage
      hasPreviousPage
    }
    edges {
      node {
        ... on Bsdasri {
          ...BsdasriFragment
        }
        ... on Bsda {
          ...BsdaFragment
        }
        ... on Bsvhu {
          ...BsvhuFragment
        }
        ... on Bspaoh {
          ...BspaohFragment
        }
        ... on Bsff {
          ...BsffFragment
        }
        ... on Form {
          ...BsddFragment
        }
      }
    }
  }
}
""")


def query_td_bordereaux_search(
    siret=None,
    tva=None,
    bsd_id=None,
    code_dechet=None,
    code_aiot=None,
    start_date_rep=None,
    end_date_rep=None,
    start_date_exp=None,
    end_date_exp=None,
    end_cursor=None,
    page_size=None,
):
    """
    Recherche multicritères de bordereaux via bordereauxSearch.
    Supporte : siret, tva, readableId, code_dechet, plages de dates réception/expédition.
    Accessible uniquement aux comptes gouvernementaux (BSDS_CAN_READ_ALL).
    """
    where_clauses = []

    if siret:
        where_clauses.append(f'clue: "{siret}"')
    elif tva:
        where_clauses.append(f'clue: "{tva}"')
    if bsd_id:
        where_clauses.append(f'readableId: "{bsd_id}"')
    if code_dechet:
        where_clauses.append(f'code_dechet: "{code_dechet}"')
    if code_aiot:
        where_clauses.append(f'code_aiot: "{code_aiot}"')
    if start_date_rep:
        where_clauses.append(f'date_reception_debut: "{start_date_rep}T00:00:00Z"')
    if end_date_rep:
        where_clauses.append(f'date_reception_fin: "{end_date_rep}T23:59:59Z"')
    if start_date_exp:
        where_clauses.append(f'date_expedition_debut: "{start_date_exp}T00:00:00Z"')
    if end_date_exp:
        where_clauses.append(f'date_expedition_fin: "{end_date_exp}T23:59:59Z"')

    where = "\n".join(where_clauses)
    after = f'after: "{end_cursor}"' if end_cursor else ""
    first = f'first: {page_size}'

    query = graphql_query_bordereaux_search.substitute(
        where=where,
        after=after,
        first=first,
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
        #print(res.json())
        return res.json()
    except (httpx.HTTPError, ValueError):
        return None

def query_td_search_companies(clue,department=None):
    """
    Requête de recherche d'entreprises dans Trackdéchets en fonction d'une "clue" qui peut être un numéro de SIRET, un numéro de TVA,
    une raison sociale ou une partie de raison sociale. La requête retourne une liste d'entreprises correspondant à la clue,
    avec leurs informations publiques (SIRET, numéro de TVA, nom, adresse, etc.).
    """
    query = """
    query SearchCompanies($clue: String!, $department: String) {
      searchCompanies(clue: $clue, department: $department, allowForeignCompanies: true) {
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
    payload = {"query": query, "variables": {"clue": clue, "department": department}}
    client = httpx.Client(timeout=30)


    def _extract_companies(response):
      data = response.json()
      if not isinstance(data, dict):
        return None
      if data.get("errors"):
        return None
      return data.get("data", {}).get("searchCompanies", [])

    auth_headers = {"Authorization": f"Bearer jLDJukhL3DaeGsjvAQcLBFzv3CNiUuBf4pZLkUBv"}

    try:
      res = client.post(url="https://api.sandbox.trackdechets.beta.gouv.fr/", headers=auth_headers, json=payload)
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
            url="https://api.sandbox.trackdechets.beta.gouv.fr/",
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