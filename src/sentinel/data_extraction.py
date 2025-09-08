import ast

import polars as pl
from django.core.cache import cache

from sentinel.constants import TAB_RESULT_PAGINATE_BY
from sentinel.queries import (
    COMPANY_ABNORMAL_COUNT_QUERY,
    COMPANY_ABNORMAL_LIST_QUERY,
    COMPANY_NO_ACTIVITY_LIST_QUERY,
    COMPANY_NOT_ON_TD_LIST_QUERY,
    NO_ACCOUNT_COMPANY_COUNT_QUERY,
    NO_ACTIVITY_COMPANY_COUNT_QUERY,
    STATS_BY_NAF_AND_DEPARTMENT_SUM_QUERY,
    STATS_BY_NAF_QUERY,
    STATS_BY_NAF_SUM_QUERY,
    WITH_ACCOUNT_COMPANY_COUNT_QUERY,
)
from sheets.data_extraction import build_query
from sheets.utils import slugify_waste_code


def parse_and_sort_dict_strings(dict_strings, descending=True):
    """Parse dictionary strings and sort by `quantity_share_ref` field"""

    sort_by = "quantity_share"

    if dict_strings is None:
        return None

    # Parse the dictionary strings
    parsed_dicts = [ast.literal_eval(dict_str) for dict_str in dict_strings]

    # Sort by the specified field
    sorted_dicts = sorted(parsed_dicts, key=lambda x: x[sort_by], reverse=descending)

    return sorted_dicts


def get_national_waste_quantity_total(naf_code):
    total = build_query(STATS_BY_NAF_SUM_QUERY, query_params={"naf_code": naf_code})

    if not len(total):
        return 0
    waste_quantity_total = round(total[0, 1])
    return waste_quantity_total


def get_dept_waste_quantity_total(naf_code, department):
    total = build_query(
        STATS_BY_NAF_AND_DEPARTMENT_SUM_QUERY, query_params={"naf_code": naf_code, "department": department}
    )

    if not len(total):
        return 0
    waste_quantity_total = round(total[0, 1])
    return waste_quantity_total


def _get_top_five_waste_code_by_naf(naf_code):
    stats_df = build_query(STATS_BY_NAF_QUERY, query_params={"naf_code": naf_code})
    return stats_df.to_dicts()


def get_top_five_waste_code_by_naf(naf_code):
    """Cache top five"""
    CACHE_DURATION = 60 * 5
    cache_key = f"national_top_five_{naf_code}"
    if cached := cache.get(cache_key):
        return cached
    res = _get_top_five_waste_code_by_naf(naf_code)
    cache.set(cache_key, res, CACHE_DURATION)
    return res


def get_no_account_company_count(naf, department):
    df = build_query(
        NO_ACCOUNT_COMPANY_COUNT_QUERY,
        query_params={
            "naf": naf,
            "department": department,
        },
    )

    return df[0, 0]


def get_no_activity_company_count(naf, department):
    df = build_query(
        NO_ACTIVITY_COMPANY_COUNT_QUERY,
        query_params={
            "naf": naf,
            "department": department,
        },
    )

    return df[0, 0]


def get_abnormal_company_count(naf, department):
    df = build_query(
        COMPANY_ABNORMAL_COUNT_QUERY,
        query_params={
            "naf": naf,
            "department": department,
        },
    )

    return df[0, 0]


def get_with_account_company_count(naf, department):
    df = build_query(
        WITH_ACCOUNT_COMPANY_COUNT_QUERY,
        query_params={
            "naf": naf,
            "department": department,
        },
    )

    return df[0, 0]


def get_company_results(query, naf, department, page=None):
    query_params = {
        "naf": naf,
        "department": department,
    }
    if page is not None:
        offset = page * TAB_RESULT_PAGINATE_BY
        query_params.update({"offset": offset, "paginate_by": TAB_RESULT_PAGINATE_BY})
        query += " LIMIT :paginate_by OFFSET :offset"

    df = build_query(
        query,
        query_params=query_params,
    )
    df = df.with_columns(
        pl.concat_str(
            [
                pl.col("address").str.strip_chars(),
                pl.col("code_postal").str.strip_chars(),
                pl.col("commune").str.strip_chars(),
            ],
            separator=" ",
        ).alias("full_address")
    )

    return df


def get_company_not_on_td_list(naf, department, page=None):
    return get_company_results(COMPANY_NOT_ON_TD_LIST_QUERY, naf, department, page)


def get_company_no_activity_list(naf, department, page=None):
    return get_company_results(COMPANY_NO_ACTIVITY_LIST_QUERY, naf, department, page)


def extract_value_for_waste_code(parsed_dicts, target_waste_code, value_field="quantity_share"):
    """Extract specific value for a given waste code from parsed_dicts"""
    if parsed_dicts is None:
        return None

    for item in parsed_dicts:
        if item["waste_code"] == target_waste_code:
            return (item["quantity_share_ref"] - item[value_field]) * 100

    # Return None or 0.0 if waste code not found
    return None


def get_company_abnormal_list(naf, department, waste_codes, page=None):
    df = get_company_results(COMPANY_ABNORMAL_LIST_QUERY, naf, department, page)
    # compute percent
    df = df.with_columns(score_percent=(pl.col("score") * 100).round(2))
    # sort `score_details` content
    df = df.with_columns(
        pl.col("score_details")
        .map_elements(
            parse_and_sort_dict_strings,
            return_dtype=pl.List(
                pl.Struct({"waste_code": pl.Utf8, "quantity_share": pl.Float64, "quantity_share_ref": pl.Float64})
            ),
        )
        .alias("parsed_score_details")
    )

    for waste_code in waste_codes:
        # Create column name (replace spaces and * with underscores for valid column names)
        col_name = slugify_waste_code(waste_code)

        df = df.with_columns(
            pl.col("parsed_score_details")
            .map_elements(
                lambda x: extract_value_for_waste_code(x, waste_code, "quantity_share"), return_dtype=pl.Float64
            )
            .alias(col_name)
        )
    df = df.drop("parsed_score_details")
    return df
