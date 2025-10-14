from string import Template

import httpx
from django.conf import settings

from .constants import TYPE_BSDA, TYPE_BSDASRI, TYPE_BSDD, TYPE_BSFF, TYPE_BSPAOH, TYPE_BSVHU

bsdd_fragment = """
fragment BsddFragment on Form {
  __typename
id
  readableId
  updatedAt
  bsddStatus: status
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
      name
    }
    workSite {
      name
    }
  }
  recipient {
    company {
      name
    }
  }
  transporters {
    company {
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
      name
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
      name
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
  }
  emitter {
    company {
      name
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
      name
    }
  }
    bsdaPackagings: packagings {
      other
      quantity
      type
    }
       waste {
      bsdaWasteCode: code
    
      materialName
 
      
      adr
  
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
  bsffUpdatedAt : updatedAt   
  bsffStatus: status

  emitter {
    company {
      name
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
      name
    }
  }
  packagings {
      numero
      type
      volume
      weight
  
  }
  bsffWeight:weight { 
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
  bsvhuUpdatedAt : updatedAt   
  weight { 
    value 
  }
  emitter {
    company {
      name
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
      name
    }
    reception {
    weight 
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
      name
    }
    emission {
    detail {weight {value}}}
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
      name
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

graphql_query_bsds = Template("""
 $bsdd_fragment
 $bsdasri_fragment
 $bsda_fragment
 $bsvhu_fragment
 $bspaoh_fragment
 $bsff_fragment
 
query GetBsds {
  bsds(
    where: {
      $where
    }
    $after
  ) {
  totalCount
    pageInfo{
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

graphql_query_bsdd_pdf = """
query BsddPdf ($id: ID!){
  formPdf(id: $id) {
  downloadLink	
  }
}
"""

graphql_query_bsdasri_pdf = """
query BsdasriPdf ($id: ID!){
  bsdasriPdf(id: $id) {
  downloadLink	
  }
}
"""

graphql_query_bsff_pdf = """
query BsffPdf ($id: ID!){
  bsffPdf(id: $id) {
  downloadLink	
  }
}
"""

graphql_query_bsda_pdf = """
query BsdaPdf ($id: ID!){
  bsdaPdf(id: $id) {
  downloadLink	
  }
}
"""
graphql_query_bsvhu_pdf = """
query BsvhuPdf ($id: ID!){
  bsvhuPdf(id: $id) {
  downloadLink	
  }
}
"""
graphql_query_bspaoh_pdf = """
query BspaohPdf ($id: ID!){
  bspaohPdf(id: $id) {
  downloadLink	
  }
}
"""


def query_td_pdf(bsd_type, bsd_id):
    configs = {
        TYPE_BSDD: {"query": graphql_query_bsdd_pdf, "field": "formPdf"},
        TYPE_BSDASRI: {"query": graphql_query_bsdasri_pdf, "field": "bsdasriPdf"},
        TYPE_BSFF: {"query": graphql_query_bsff_pdf, "field": "bsffPdf"},
        TYPE_BSDA: {"query": graphql_query_bsda_pdf, "field": "bsdaPdf"},
        TYPE_BSPAOH: {"query": graphql_query_bspaoh_pdf, "field": "bspaohPdf"},
        TYPE_BSVHU: {"query": graphql_query_bsvhu_pdf, "field": "bsvhuPdf"},
    }

    config = configs.get(bsd_type)
    query = config["query"]
    field = config["field"]
    client = httpx.Client(timeout=60)
    res = client.post(
        url=settings.TD_API_URL,
        headers={"Authorization": f"Bearer {settings.TD_API_TOKEN}"},
        json={
            "query": query,
            "variables": {
                "id": bsd_id,
            },
        },
    )
    rep = res.json()

    link = rep.get("data", {}).get(field, {}).get("downloadLink", None)

    return link


graphql_query_control_bsds = Template("""
 $bsdd_fragment
 $bsdasri_fragment
 $bsda_fragment
 $bsvhu_fragment
 $bspaoh_fragment
 $bsff_fragment

query ControlBsds {
  controlBsds(
    where: {
      $where
    }
    $after
  ) {
  totalCount
    pageInfo{
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


def query_td_control_bsds(siret=None, plate=None, bsd_id=None, start_cursor=None, end_cursor=None):
    """Request SENT bsds matching siret and plate. Vhu do not have plates yet and are ignored"""

    where = ""
    after = ""
    if siret:
        where += f' siret: "{siret}" '
    if plate:
        where += f' plate: "{plate}" '
    if bsd_id:
        where += f' readableId: "{bsd_id}" '
    if end_cursor:
        after = f'after: "{end_cursor}"'

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
            json={
                "query": query,
                "variables": {
                    "siret": siret,
                    "plate": plate,
                },
            },
        )

        rep = res.json()

    except httpx.HTTPError:
        return []

    return rep
