from django.urls import path

from .api import ApiCompanyExport, ApiObjects, ICPEFrance, ICPEGraph, ICPEViewMany
from .views import ExutMapView, MapView, IcpeMapView

urlpatterns = [
    path("", MapView.as_view(), name="map_view"),
    path("api/companies/objects", ApiObjects.as_view(), name="map_api_objects"),
    path("api/companies/export", ApiCompanyExport.as_view(), name="map_api_export"),
    path("icpe", IcpeMapView.as_view(), name="new_icpe_map_view"),
    path("exutoires", ExutMapView.as_view(), name="icpe_map_view"),
    path("api/icpe/france/<int:year>/<str:rubrique>", ICPEFrance.as_view(), name="icpe_france"),
    path("api/icpe/<str:layer>/<int:year>/<str:rubrique>", ICPEViewMany.as_view(), name="icpe_many"),
    path("api/icpe/<str:layer>/<int:year>/<str:rubrique>/<str:code>", ICPEGraph.as_view(), name="icpe_get_graph"),
]
