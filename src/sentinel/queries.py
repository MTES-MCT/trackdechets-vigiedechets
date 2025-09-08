STATS_BY_NAF_SUM_QUERY = """
                         SELECT ape_code,
                                SUM(waste_quantity) as total_waste_quantity
                         FROM refined_zone_vigiedechets.sentinelle_waste_quantity_produced_by_ape_code
                         WHERE ape_code = :naf_code
                         GROUP BY ape_code
                         """

STATS_BY_NAF_AND_DEPARTMENT_SUM_QUERY = """
                                        SELECT ape_code,
                                               SUM(waste_quantity) as total_waste_quantity
                                        FROM refined_zone_vigiedechets.sentinelle_waste_quantity_produced_by_ape_code_departement
                                        where code_departement = :department
                                          AND ape_code = :naf_code
                                        GROUP BY ape_code
                                        """

STATS_BY_NAF_QUERY = """
                     SELECT ape_code,
                            waste_code,
                            waste_quantity,
                            waste_quantity_share
                     FROM refined_zone_vigiedechets.sentinelle_waste_quantity_produced_by_ape_code
                     WHERE ape_code = :naf_code
                       AND ROUND(waste_quantity_share, 3) > 0
                     ORDER BY waste_quantity_share DESC LIMIT 5
                     """

STATS_BY_NAF_AND_DEPARTMENT_QUERY = """
                                    SELECT ape_code,
                                           waste_code,
                                           waste_quantity_share
                                    FROM refined_zone_vigiedechets.sentinelle_waste_quantity_produced_by_ape_code_departement
                                    WHERE ape_code = :naf_code
                                      and code_departement = :department
                                      AND ROUND(waste_quantity_share, 3) > 0
                                    ORDER BY waste_quantity_share DESC LIMIT 5
                                    """

NO_ACCOUNT_COMPANY_COUNT_QUERY = """
                                 SELECT count(*)
                                 from refined_zone_vigiedechets.sentinelle_companies_without_account
                                 where company_code_departement = :department
                                   AND company_ape_code = :naf
                                 """

# NO_ACCOUNT_COMPANY_BY_DEPT_COUNT_QUERY = """
#                                  SELECT count(*)
#                                  from refined_zone_vigiedechets.sentinelle_companies_without_account
#                                  where company_code_departement = :department
#                                  """

WITH_ACCOUNT_COMPANY_COUNT_QUERY = r"""
                                   SELECT count()
                                   from refined_zone_vigiedechets.sentinelle_waste_quantity_produced_by_siret
                                   where company_code_departement = :department
                                     AND company_ape_code = :naf
                                   """

NO_ACTIVITY_COMPANY_COUNT_QUERY = r"""
                                  SELECT count()
                                  from refined_zone_vigiedechets.sentinelle_companies_without_activity
                                  where company_code_departement = :department
                                    AND company_ape_code = :naf
                                  """


COMPANY_ABNORMAL_COUNT_QUERY = r"""
                               SELECT COUNT()
                               from refined_zone_vigiedechets.sentinelle_companies_scores
                               where company_code_departement = :department
                                 AND company_ape_code = :naf
                               """

COMPANY_NOT_ON_TD_LIST_QUERY = r"""
                               SELECT company_siret           as siret,
                                      company_name            as name,
                                      company_address         as address,
                                      company_code_postal     as code_postal,
                                      company_libelle_commune as commune
                               from refined_zone_vigiedechets.sentinelle_companies_without_account
                               where company_code_departement = :department
                                 AND company_ape_code = :naf
                               ORDER BY company_siret"""

COMPANY_NO_ACTIVITY_LIST_QUERY = r"""
                                 SELECT company_siret           as siret,
                                        company_name            as name,
                                        company_address         as address,
                                        company_code_postal     as code_postal,
                                        company_libelle_commune as commune

                                 from refined_zone_vigiedechets.sentinelle_companies_without_activity
                                 where company_code_departement = :department
                                   AND company_ape_code = :naf
                                 ORDER BY company_siret"""

COMPANY_ABNORMAL_LIST_QUERY = r"""
                              SELECT company_siret           as siret,
                                     company_name            as name,
                                     company_address         as address,
                                     company_code_postal     as code_postal,
                                     company_libelle_commune as commune,
                                     score,
                                     score_details,
                              from refined_zone_vigiedechets.sentinelle_companies_scores
                              where company_code_departement = :department
                                AND company_ape_code = :naf
                              order by score DESC"""
