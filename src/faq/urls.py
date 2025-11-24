from django.urls import path

from .views import (
    AssistanceContactView,
    AssistanceMessageSentView,
    AssistancePageView,
    AssistanceWrapperView,
    FaqPageView,
    FaqSearchView,
    FaqView,
    webinar_link,
)

urlpatterns = [
    path("", FaqView.as_view(), name="faq_home"),
    path("<int:pk>/", FaqView.as_view(), name="faq"),
    path("page/<int:pk>/", FaqPageView.as_view(), name="faq_page"),
    path("search/", FaqSearchView.as_view(), name="faq_page_search"),
    path("assistance/", AssistanceWrapperView.as_view(), name="assistance_wrapper_home"),
    path("assistance/<int:pk>/", AssistanceWrapperView.as_view(), name="assistance_wrapper_page"),
    path("assistance/page/<int:pk>/", AssistancePageView.as_view(), name="assistance_page"),
    path("assistance/contact/", AssistanceContactView.as_view(), name="assistance_contact"),
    path("assistance/message-sent/", AssistanceMessageSentView.as_view(), name="assistance_message_sent"),
    path("webinar/<uuid:pk>", webinar_link, name="webinar_ics"),
]
