from typing import TypedDict

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
