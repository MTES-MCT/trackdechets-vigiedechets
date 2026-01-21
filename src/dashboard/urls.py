from django.urls import path

from .views import DashboardView, MetabaseProxyView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("proxy/<path:path>", MetabaseProxyView.as_view(), name="metabase_proxy"),
]
