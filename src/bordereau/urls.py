from django.urls import path

from .views import (
    BsdSearch,
    BsdSimpleSearch,
    BsdAdvancedSearch,
    CompanySearchView,
    BsdSearchResult,
    BsdRecentSearch,
)

urlpatterns = [
    path("bsd-search/", BsdSearch.as_view(), name="bordereau_search"),
    path("bsd-simple-search/", BsdSimpleSearch.as_view(), name="bordereau_simple_search"),
    path("bsd-advanced-search/", BsdAdvancedSearch.as_view(), name="bordereau_advanced_search"),
    path("company-search/", CompanySearchView.as_view(), name="bordereau_company_search"),
    path("bsd-search-result/", BsdSearchResult.as_view(), name="bordereau_search_result"),
    path("bsd-recent-search/", BsdRecentSearch.as_view(), name="bordereau_recent_search"),
]