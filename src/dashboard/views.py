from django.views.generic import TemplateView

from common.mixins import FullyLoggedMixin
from accounts.constants import PERMS_DASHBOARD
from common.constants import SSHTarget
from common.ssh import ssh_tunnel, get_tunnel_port
from django.conf import settings
from .metabase import get_metabase_iframe_url


class DashboardView(FullyLoggedMixin, TemplateView):
    template_name = "dashboard/dashboard.html"
    allowed_user_categories = PERMS_DASHBOARD

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ssh_tunnel(settings, SSHTarget.METABASE)

        tunnel_port = get_tunnel_port()
        context["iframe_url"] = get_metabase_iframe_url(tunnel_port=tunnel_port)
        return context
