from django.conf import settings
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import SearchHeadline, SearchQuery, SearchRank, SearchVector
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http.response import Http404, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import FormView
from django_htmx.http import push_url, trigger_client_event

from common.mixins import FullyLoggedMixin, HtmxOnlyMixin

from .forms import ContactForm, FaqSearchForm
from .models import AssistancePage, FaqPage, Message, Webinar


class FaqView(FullyLoggedMixin, TemplateView):
    allowed_user_categories = ["*"]
    template_name = "faq/faq.html"

    def get_context_data(self, **kwargs):
        faq_pages = FaqPage.objects.for_user(self.request.user)
        current_page = None
        if faq_pk := self.kwargs.get("pk", None):
            current_page = faq_pages.filter(pk=faq_pk).first()
        if not faq_pk or not current_page:
            current_page = faq_pages.first()

        return super().get_context_data(**kwargs, faq_pages=faq_pages, current_page=current_page)


class FaqPageView(HtmxOnlyMixin, FullyLoggedMixin, DetailView):
    allowed_user_categories = ["*"]
    model = FaqPage
    template_name = "faq/faq_page.html"
    context_object_name = "page"

    def get_queryset(self):
        return super().get_queryset().for_user(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if getattr(self, "object", None):
            response = push_url(response, reverse_lazy("faq", args=[self.object.pk]))
        response = trigger_client_event(response, "highlightNavigation", after="settle")  # trigger after url push
        return response

    def get_context_data(self, **kwargs):
        user_category = self.request.user.user_category
        # filter suggestions to only display allowed pages
        suggested_pages = self.object.suggestions.filter(
            Q(linked_page__user_categories__contains=[user_category]) | Q(linked_page__user_categories=[])
        )

        return super().get_context_data(**kwargs, suggested_pages=suggested_pages)


language = "french_unaccent"


class FaqSearchView(HtmxOnlyMixin, FullyLoggedMixin, FormView):
    """Search view for FAQ pages with filtering capabilities"""

    allowed_user_categories = ["*"]
    template_name = "faq/faq_page_search_results.html"

    form_class = FaqSearchForm
    success_url = reverse_lazy("faq_page_search")

    def get_queryset(self):
        base_queryset = FaqPage.objects.for_user(self.request.user)
        form = FaqSearchForm(self.request.GET)

        if not form.is_valid():
            return base_queryset.none()

        search_query = form.cleaned_data.get("q", "").strip()

        if not search_query:
            return base_queryset.select_related("parent").order_by("position")

        search_type = "plain"
        language = "french_unaccent"

        # Create search query
        search_query_obj = SearchQuery(search_query, config=language, search_type=search_type)

        # Ssearch vectors for title and aggregated content blocks
        search_vector = SearchVector("title", weight="A", config=language) + SearchVector(
            StringAgg("blocks__content", delimiter=" "), weight="B", config=language
        )

        # Annotate with search rank for ordering
        queryset = base_queryset.annotate(
            search=search_vector, rank=SearchRank(search_vector, search_query_obj, cover_density=True)
        ).filter(search=search_query_obj)

        if queryset.count() > 0:
            # Add headline highlighting for title
            queryset = queryset.annotate(
                highlighted_title=SearchHeadline(
                    "title", search_query_obj, start_sel="<mark>", stop_sel="</mark>", config=language
                ),
                snippet=SearchHeadline(
                    StringAgg("blocks__content", delimiter=" "),
                    search_query_obj,
                    start_sel="<mark>",
                    stop_sel="</mark>",
                    max_words=30,
                    min_words=15,
                    config=language,
                ),
            )

            # Order by ranks
            queryset = queryset.order_by("-rank", "position")

        return queryset.prefetch_related("blocks")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_query"] = self.request.GET.get("q", "")

        results = self.get_queryset()
        context["results"] = results
        context["result_count"] = len(results)

        return context


class AssistanceWrapperView(FullyLoggedMixin, TemplateView):
    template_name = "faq/assistance_wrapper.html"
    allowed_user_categories = ["*"]

    def get_context_data(self, **kwargs):
        assistance_pages = AssistancePage.objects.all().order_by("level")
        current_page = None

        if page_pk := self.kwargs.get("pk", None):
            current_page = assistance_pages.filter(pk=page_pk).first()
        if not page_pk or not current_page:
            current_page = assistance_pages.first()

        return super().get_context_data(**kwargs, assistance_pages=assistance_pages, current_page=current_page)


class AssistancePageView(HtmxOnlyMixin, FullyLoggedMixin, DetailView):
    model = AssistancePage
    template_name = "faq/assistance_page.html"
    context_object_name = "page"
    allowed_user_categories = ["*"]

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if getattr(self, "object", None):
            response = push_url(response, reverse_lazy("assistance_wrapper_page", args=[self.object.pk]))
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        form = ContactForm()
        ctx.update({"form": form})
        return ctx


class AssistanceContactView(HtmxOnlyMixin, FullyLoggedMixin, FormView):
    form_class = ContactForm
    success_url = reverse_lazy("assistance_message_sent")
    template_name = "dummy.html"
    allowed_user_categories = ["*"]

    def get(self, request, *args, **kwargs):
        raise Http404()

    def form_valid(self, form):
        res = super().form_valid(form)
        data = form.cleaned_data
        user = self.request.user
        username = self.request.user.username
        user_email = user.email

        body_content = data["body"]
        subject = data["subject"]
        assistance_page_title = data["assistance_page_title"]
        body = [
            f"Nom: {username}",
            f"Page d'origine: {assistance_page_title}",
            f"Message: {body_content}",
        ]

        # Build and send message
        message = EmailMessage(
            subject=subject,
            body="\n\n".join(body),
            from_email=user_email,
            to=[settings.SUPPORT_FORM_RECIPIENT],
        )

        if self.request.FILES:
            for uploaded_file in self.request.FILES.getlist("files"):
                message.attach(uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)

        message.send()

        # Save message data
        Message.objects.create(
            user=self.request.user,
            subject=subject,
            message=body_content,
            origin_page_title=assistance_page_title,
            ip=self.get_client_ip(),
        )
        return res

    def get_client_ip(self):
        x_forwarded_for = self.request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR")
        return ip


class AssistanceMessageSentView(HtmxOnlyMixin, FullyLoggedMixin, TemplateView):
    allowed_user_categories = ["*"]
    template_name = "faq/assistance_message_sent.html"


def webinar_link(request, pk):
    event = Webinar.objects.get(pk=pk)
    response = HttpResponse(event.as_ics(), content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f"attachment; filename={event.slug}.ics"
    return response
