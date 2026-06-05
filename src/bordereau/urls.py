from django.urls import path
from .views import (
    BsdSearch,
    CompanySearchView,
    BsdSearchResultById,
    BsdSearchResult,
    BsdPdfBundle,
    BsdBundleProcessingView,
    BsdFragmentBundleProcessingView,
    BsdPdfBundleResult,
    BsdRecentSearch,
    SingleBordereauPdfDownload,
)

urlpatterns = [
    path("bsd-search/", BsdSearch.as_view(), name="bordereau_search"),
    path("recent-bordereau-pdfs/", BsdRecentSearch.as_view(), name="bordereau_recent_pdfs"),
    path("company-search/", CompanySearchView.as_view(), name="bordereau_company_search"),
    path("bsd-search-result/", BsdSearchResult.as_view(), name="bordereau_search_result"),
    path("bsd-id-search-result/", BsdSearchResultById.as_view(), name="bordereau_bsd_id_search_result"),
    path("single-pdf-download/", SingleBordereauPdfDownload.as_view(), name="bordereau_single_bsd_pdf_download"),
    path(
        "bsd-search/pdf-bundle-process/",
        BsdPdfBundle.as_view(),
        name="bordereau_pdf_bundle",
    ),
    path(
        "bsd-search/pdf-bundle-processing/<str:task_id>/<uuid:bundle_pk>/",
        BsdBundleProcessingView.as_view(),
        name="bordereau_pdf_bundle_processing",
    ),
    path(
        "bsd-search/pdf-bundle-processing-fragment/<str:task_id>/<uuid:bundle_pk>/",
        BsdFragmentBundleProcessingView.as_view(),
        name="bordereau_pdf_bundle_processing_fragment",
    ),
    path(
        "bsd-search/pdf-bundle-result/<uuid:pk>/",
        BsdPdfBundleResult.as_view(),
        name="bordereau_pdf_bundle_result",
    ),
]