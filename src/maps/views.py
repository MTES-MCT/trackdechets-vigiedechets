from django.views.generic import TemplateView

from accounts.constants import PERMS_MAP, PERMS_MAP_ICPE
from common.mixins import FullyLoggedMixin


class MapView(FullyLoggedMixin, TemplateView):
    template_name = "maps/map.html"
    allowed_user_categories = PERMS_MAP


class ExutMapView(FullyLoggedMixin, TemplateView):
    template_name = "maps/icpe_map.html"
    allowed_user_categories = PERMS_MAP_ICPE


class IcpeMapView(FullyLoggedMixin, TemplateView):
    template_name = "maps/new_icpe_map.html"
    allowed_user_categories = PERMS_MAP_ICPE
