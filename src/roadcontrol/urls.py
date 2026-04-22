from django.urls import path

from .views import (
    BsdRecentPdfs,
    BsdSearch,
    BsdSimpleSearch,
    BsdAdvancedSearch,
    CompanySearchView,
    BsdSearchResult,
    BundleProcessingView,
    FragmentBundleProcessingView,
    NoResultRoadControlPdf,
    RoadControlPdfBundle,
    RoadControlPdfBundleResult,
    RoadControlRecentPdfs,
    RoadControlSearch,
    RoadControlSearchResult,
    SingleBsdPdfDownload,
)

urlpatterns = [
    path("", RoadControlSearch.as_view(), name="roadcontrol"),
    path("search-result/", RoadControlSearchResult.as_view(), name="roadcontrol_search_result"),
    path("pdf/", SingleBsdPdfDownload.as_view(), name="single_bsd_pdf_download"),
    path("no-result-pdf/", NoResultRoadControlPdf.as_view(), name="no_result_roadcontrol_pdf"),
    path("pdf-bundle-process/", RoadControlPdfBundle.as_view(), name="roadcontrol_pdf_bundle"),
    path(
        "pdf-bundle-processing/<str:task_id>/<uuid:bundle_pk>/",
        BundleProcessingView.as_view(),
        name="roadcontrol_pdf_bundle_processing",
    ),
    path(
        "pdf-bundle-processing-fragment/<str:task_id>/<uuid:bundle_pk>/",
        FragmentBundleProcessingView.as_view(),
        name="pdf_bundle_processing_fragment",
    ),
    path("pdf-bundle-result/<str:pk>/", RoadControlPdfBundleResult.as_view(), name="roadcontrol_pdf_bundle_result"),
    path("recent-road-control-pdfs/", RoadControlRecentPdfs.as_view(), name="roadcontrol_recent_pdfs"),
    path("recent-bsd-pdfs/", BsdRecentPdfs.as_view(), name="bsd_recent_pdfs"),
    path("bsd-search/", BsdSearch.as_view(), name="roadcontrol_bsd_search"),
    path("bsd-simple-search/", BsdSimpleSearch.as_view(), name="roadcontrol_bsd_simple_search"),
    path("bsd-advanced-search/", BsdAdvancedSearch.as_view(), name="roadcontrol_bsd_advanced_search"),
    path("company-search/", CompanySearchView.as_view(), name="roadcontrol_company_search"),
    path("bsd-search-result/", BsdSearchResult.as_view(), name="roadcontrol_bsd_search_result"),
]
