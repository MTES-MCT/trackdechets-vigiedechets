"""Vigiedéchets URL Configuration"""

from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import Http404
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from django_otp.admin import OTPAdminSite

from dashboard.views import MetabaseStaticProxyView
from sheets.views import PrivateHomeView, PublicHomeView

# Admin config
admin.site.index_title = "Administration de Vigiedéchets"
admin.site.__class__ = OTPAdminSite


def not_found(request):
    raise Http404()


urlpatterns = [
    path(
        "favicon.ico",
        RedirectView.as_view(permanent=True, url=staticfiles_storage.url("img/favicon.ico")),
    ),
    path(f"{settings.ADMIN_SLUG}/login/", not_found),  # disable admin logout
    path("grappelli/", include("grappelli.urls")),  # grappelli URLS
    path(f"{settings.API_SLUG}/api/v1/", include("api.urls")),
    path(f"{settings.ADMIN_SLUG}/", admin.site.urls),
    path("", PublicHomeView.as_view(), name="public_home"),
    path("home/", PrivateHomeView.as_view(), name="private_home"),
    path("local-accounts/", include("accounts.urls")),
    path(
        "accounts/monaiot/login/",
        RedirectView.as_view(pattern_name="monaiot_oidc_authentication_init"),
        name="former_monaiot_init",
    ),
    path("oidc/", include("oidc.urls")),
    path("content/", include("content.urls")),
    path("sheets/", include("sheets.urls")),
    path("registry/", include("registry.urls")),
    path("roadcontrol/", include("roadcontrol.urls")),
    path("map/", include("maps.urls")),
    path("data-exports/", include("data_exports.urls")),
    path("sentinelle/", include("sentinel.urls")),
    path("faq/", include("faq.urls")),
    path("dashboard/", include("dashboard.urls")),
    # Metabase static assets - these are requested with absolute /app/* paths by the embed
    re_path(r"^app/(?P<path>.*)$", MetabaseStaticProxyView.as_view(), name="metabase_static"),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
