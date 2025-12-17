from django.views.generic import TemplateView

from accounts.constants import PERMS_MAP
from common.mixins import FullyLoggedMixin


class GalaxyView(FullyLoggedMixin, TemplateView):
    template_name = "galaxy/galaxy.html"
    allowed_user_categories = PERMS_MAP
