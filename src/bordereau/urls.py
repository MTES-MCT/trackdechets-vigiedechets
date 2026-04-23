from django.urls import path

from .views import (
    BsdSearch,
    BsdSimpleSearch,
    BsdAdvancedSearch,
    CompanySearchView,
    BsdSearchResult,
)

urlpatterns = [
    path("bsd-search/", BsdSearch.as_view(), name="bsd_search"),
    path("bsd-simple-search/", BsdSimpleSearch.as_view(), name="bsd_simple_search"),
    path("bsd-advanced-search/", BsdAdvancedSearch.as_view(), name="bsd_advanced_search"),
    path("company-search/", CompanySearchView.as_view(), name="company_search"),
    path("bsd-search-result/", BsdSearchResult.as_view(), name="bsds_search_result"),
]