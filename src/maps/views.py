import json

from django.http import Http404
from django.views.generic import TemplateView

from accounts.constants import PERMS_MAP, PERMS_MAP_ICPE
from common.mixins import FullyLoggedMixin
from maps.models import InstallationsComputation, DepartementsComputation, RegionsComputation, FranceComputation


class MapView(FullyLoggedMixin, TemplateView):
    template_name = "maps/map.html"
    allowed_user_categories = PERMS_MAP


class ExutMapView(FullyLoggedMixin, TemplateView):
    template_name = "maps/icpe_map.html"
    allowed_user_categories = PERMS_MAP_ICPE


class IcpeMapView(FullyLoggedMixin, TemplateView):
    template_name = "maps/new_icpe_map.html"
    allowed_user_categories = PERMS_MAP_ICPE


class ICPEGraphView(FullyLoggedMixin, TemplateView):
    template_name = "maps/graph.html"
    allowed_user_categories = PERMS_MAP_ICPE

    def get(self, request, layer, year, rubrique, code, *args, **kwargs):
        self.layer = layer
        self.rubrique = rubrique
        self.code = code
        self.year = year

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        layers_configs = {
            "france": {
                "cls": FranceComputation,
                "specific_filter": { },
            },
            "installations": {
                "cls": InstallationsComputation,
                "specific_filter": {"code_aiot": self.code},
            },
            "departements": {
                "cls": DepartementsComputation,
                "specific_filter": {"code_departement_insee": self.code},
            },
            "regions": {
                "cls": RegionsComputation,
                "specific_filter": {"code_region_insee": self.code},
            },
        }

        layer_config = layers_configs[self.layer]
        model = layer_config["cls"]
        specific_filter = layer_config["specific_filter"]
        result = model.objects.filter(year=self.year, rubrique=self.rubrique, **specific_filter).first()
        if not result:
            raise Http404


        return super().get_context_data(**kwargs, result=result )
