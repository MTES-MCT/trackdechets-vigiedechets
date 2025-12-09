import re

import numpy as np
import pandas as pd

from sheets.constants import BSDASRI, BSFF, COLLECTOR_TYPES, COMPANY_TYPES, WASTE_PROCESSOR_TYPES


def get_code_departement(postal_code: str) -> str:
    """Take a postal code and returns the département code."""
    if pd.isna(postal_code):
        return np.nan
    if 20000 <= int(postal_code) < 21000:
        if int(postal_code) <= 20190:
            return "2A"
        else:
            return "2B"
    if int(postal_code) > 97000:
        return postal_code[:3]

    return postal_code[:2]


def format_number_str(input_number: float, precision: int = 2, default_value: str = "0") -> str:
    """Format a float to a string with thousands separated by space and rounding it at the given precision."""
    if not input_number:
        return default_value

    input_number = round(input_number, precision)

    return re.sub(r"\.0*$", "", "{:,}".format(input_number).replace(",", " "))


def to_verbose_company_types(db_company_types):
    return [COMPANY_TYPES.get(ct) for ct in db_company_types if ct in COMPANY_TYPES.keys()]


def to_verbose_collector_types(db_collector_types):
    if db_collector_types is None:
        return []
    return [COLLECTOR_TYPES.get(ct) for ct in db_collector_types if ct in COLLECTOR_TYPES.keys()]


def to_verbose_waste_processor_types(db_waste_processor_types):
    if db_waste_processor_types is None:
        return []
    return [WASTE_PROCESSOR_TYPES.get(ct) for ct in db_waste_processor_types if ct in WASTE_PROCESSOR_TYPES.keys()]


def get_quantity_variable_names(bs_type):
    quantity_variables = ["quantity_received"]
    if bs_type == BSDASRI:
        quantity_variables = ["quantity_received", "volume"]
    if bs_type == BSFF:
        quantity_variables = ["acceptation_weight"]
    return quantity_variables


def slugify_waste_code(waste_code):
    """Create proper python var name from waste code"""
    return f"waste_{waste_code.replace(' ', '_').replace('*', '_star')}"
