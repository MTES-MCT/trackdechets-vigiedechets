from django.urls import path

from .views import FaqView, PageView, FaqSearchView

urlpatterns = [
    path("", FaqView.as_view(), name="faq_home"),
    path("<int:pk>/", FaqView.as_view(), name="faq"),
    path("page/<int:pk>/", PageView.as_view(), name="faq_page"),
    path("search/", FaqSearchView.as_view(), name="faq_page_search"),
]
