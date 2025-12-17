from django.urls import path

from .api import GalaxyGraphAPI
from .views import GalaxyView

urlpatterns = [
    path("", GalaxyView.as_view(), name="galaxy_view"),
    path("api/graph", GalaxyGraphAPI.as_view(), name="galaxy_api_graph"),
]
