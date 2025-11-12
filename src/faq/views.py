from django.urls import reverse_lazy
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import FormView

from common.mixins import FullyLoggedMixin
from .forms import FaqSearchForm

from django.contrib.postgres.aggregates import StringAgg
from django.db.models import F, Value, FloatField
from django.db.models.functions import Coalesce
from django.db.models import Max

from .models import FaqPage
from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank, SearchHeadline, TrigramSimilarity
)


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


class PageView(FullyLoggedMixin, DetailView):
    allowed_user_categories = ["*"]
    model = FaqPage
    template_name = "faq/page.html"
    context_object_name = "page"

    def get_queryset(self):
        return super().get_queryset().for_user(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        response["HX-Push-Url"] = reverse_lazy("faq", args=[self.object.pk])
        response["HX-Trigger-After-Settle"] = "highlightNavigation"  # trigger after url push

        return response


language = "french_unaccent"


class FaqSearchView(FormView):
    """Search view for FAQ pages with filtering capabilities"""

    template_name = "faq/page_search_results.html"

    form_class = FaqSearchForm
    success_url = reverse_lazy("faq_page_search")

    def get_queryset(self):
        base_queryset = FaqPage.objects.for_user(self.request.user)
        form = FaqSearchForm(self.request.GET)

        if not form.is_valid():
            return base_queryset.none()

        search_query = form.cleaned_data.get('q', '').strip()

        if not search_query:
            return base_queryset.select_related('parent').order_by('position')

        search_type = 'plain'
        language = 'french_unaccent'

        # Create search query
        search_query_obj = SearchQuery(
            search_query,
            config=language,
            search_type=search_type
        )

        # Ssearch vectors for title and aggregated content blocks
        search_vector = (
                SearchVector('title', weight='A', config=language) +
                SearchVector(
                    StringAgg('blocks__content', delimiter=' '),
                    weight='B',
                    config=language
                )
        )

        # Annotate with search rank for ordering
        queryset = base_queryset.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, search_query_obj, cover_density=True)
        ).filter(
            search=search_query_obj
        )

        if queryset.count() > 0:
            # Add headline highlighting for title
            queryset = queryset.annotate(
                highlighted_title=SearchHeadline(
                    'title',
                    search_query_obj,
                    start_sel='<mark>',
                    stop_sel='</mark>',
                    config=language
                ),
                snippet=SearchHeadline(
                    StringAgg('blocks__content', delimiter=' '),
                    search_query_obj,
                    start_sel='<mark>',
                    stop_sel='</mark>',
                    max_words=30,
                    min_words=15,
                    config=language
                )
            )

            # Order by ranks
            queryset = queryset.order_by('-rank', 'position')

        return queryset.prefetch_related('blocks')

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['search_query'] = self.request.GET.get('q', '')


        results =  self.get_queryset()
        context['results'] =results
        context['result_count'] = len(results)

        return context
