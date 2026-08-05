from typing import TypedDict

import httpx
from django.conf import settings
from sqlalchemy.sql import text

from sheets.data_extraction import get_wh_sqlachemy_engine

sql_company_query_data_str = """
select
    name, address, contact, contact_email, contact_phone 
 from
    trusted_zone_trackdechets.company
where
    siret = :siret ;
"""


class CompanyData(TypedDict):
    company_name: str
    company_address: str
    company_contact: str
    company_email: str
    company_phone: str


def get_company_data(siret) -> CompanyData:
    """
    prepared_query = text(sql_company_query_data_str)

    wh_engine = get_wh_sqlachemy_engine()
    with wh_engine.connect() as con:
        companies = con.execute(prepared_query, {"siret": siret}).all()

    company = companies[0]
    return {
        "company_name": company[0] or "",
        "company_address": company[1] or "",
        "company_contact": company[2] or "",
        "company_email": company[3] or "",
        "company_phone": company[4] or "",
    }
    """
    query = """
    query SearchCompanies($clue: String!) {
      searchCompanies(clue: $clue, allowForeignCompanies: true) {
        siret
        vatNumber
        name
        address
        contact
        contactEmail
        contactPhone
      }
    }
    """
    payload = {"query": query, "variables": {"clue": siret}}
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

        if companies:
            company = companies[0]
            return {
                "company_name": company.get("name", ""),
                "company_address": company.get("address", ""),
                "company_contact": company.get("contact", ""),
                "company_email": company.get("contactEmail", ""),
                "company_phone": company.get("contactPhone", ""),
            }
    except (httpx.HTTPError, ValueError):
        pass

    return {
        "company_name": "Établissement inconnu",
        "company_address": "Adresse non renseignée",
        "company_contact": "",
        "company_email": "",
        "company_phone": "",
    }
