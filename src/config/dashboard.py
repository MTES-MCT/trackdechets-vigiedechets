from django.utils.translation import gettext_lazy as _
from grappelli.dashboard import Dashboard, modules


class RecentUsers(modules.DashboardModule):
    """
    Module that lists the recent subscribed users.
    """

    title = _("Derniers utilisateurs inscrits")
    template = "admin/recent_users.html"
    limit = 10
    include_list = None
    exclude_list = None

    def __init__(self, **kwargs):
        super().__init__(self.title, **kwargs)

    def init_with_context(self, context):
        if self._initialized:
            return

        from accounts.models import User

        qs = User.objects.order_by("-date_joined")[: self.limit]

        self.children = qs[: self.limit]
        self._initialized = True


class RecentSheets(modules.DashboardModule):
    """
    Module that lists the recent created sheetsr.
    """

    title = _("Dernières fiches établissement")
    template = "admin/recent_sheets.html"
    limit = 10
    include_list = None
    exclude_list = None

    def __init__(self, **kwargs):
        super().__init__(self.title, **kwargs)

    def init_with_context(self, context):
        if self._initialized:
            return

        from sheets.models import ComputedInspectionData

        qs = ComputedInspectionData.objects.order_by("-created")[: self.limit]

        self.children = qs[: self.limit]
        self._initialized = True


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard.
    """

    template = "admin/dashboard.html"

    def init_with_context(self, context):
        self.children.append(
            modules.ModelList(
                _("Suivi"),
                column=1,
                collapsible=False,
                models=(
                    "accounts.*",
                    "sheets.*",
                    "registry.models.RegistryV2Export",
                ),
            )
        )
        self.children.append(
            modules.ModelList(
                _("Faq & bannière"),
                column=1,
                collapsible=False,
                models=("faq.*", "common.*"),
            )
        )

        self.children.append(
            modules.AppList(
                _("Accès développeurs"),
                collapsible=True,
                column=1,
                css_classes=("collapse closed grp-closed",),
            )
        )

        self.children.append(
            RecentUsers(
                limit=10,
                collapsible=False,
                column=2,
            )
        )
        self.children.append(
            RecentSheets(
                limit=10,
                collapsible=False,
                column=2,
            )
        )

        self.children.append(
            modules.RecentActions(
                _("Recent actions"),
                limit=5,
                collapsible=False,
                column=3,
            )
        )
