from django.views.generic import TemplateView

from common.mixins import FullyLoggedMixin
from accounts.constants import PERMS_DASHBOARD
from .metabase import get_metabase_iframe_url


class DashboardView(FullyLoggedMixin, TemplateView):
    template_name = "dashboard/dashboard.html"
    allowed_user_categories = PERMS_DASHBOARD

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["iframe_url"] = get_metabase_iframe_url()
        return context
