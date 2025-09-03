import io

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from common.mixins import FullyLoggedMixin
from maps.centroids import DEPARTMENTS_CENTROIDS

from .constants import ABNORMAL, NO_ACTIVITY, NON_REGISTERED, TAB_RESULT_PAGINATE_BY
from .data_extraction import (
    get_abnormal_company_count,
    get_company_abnormal_list,
    get_company_no_activity_list,
    get_company_not_on_td_list,
    get_no_account_company_count,
    get_no_activity_company_count,
    get_top_five_waste_code_by_naf,
    get_with_account_company_count,
)
from .forms import NafSearchForm
from .graphs import build_department_graph, build_national_graph
from .naf_codes import NAF_CODES


class SentinelEmailAccessMixin:
    allowed_user_emails = settings.ALLOWED_USER_FOR_SENTINEL


class Sentinel(SentinelEmailAccessMixin, FullyLoggedMixin, TemplateView):
    template_name = "sentinel/sentinel.html"

    def get_context_data(self, **kwargs):
        form = NafSearchForm()
        return super().get_context_data(**kwargs, form=form)


def get_naf_code_label(naf_code):
    return next((item["label"] for item in NAF_CODES if item["id"] == naf_code), None)


def get_naf_code_full_label(naf_code):
    return f"{naf_code} {get_naf_code_label(naf_code)}"


def get_department_label(department):
    return DEPARTMENTS_CENTROIDS.get(department).get("name")


class ResultWrapper(SentinelEmailAccessMixin, FullyLoggedMixin, FormView):
    template_name = "sentinel/partials/_result_wrapper.html"

    form_class = NafSearchForm
    naf_code = None

    def form_valid(self, form):
        self.naf_code = form.cleaned_data.get("selected_naf_code")
        self.department = form.cleaned_data.get("department")
        # set in cache for child components
        get_top_five_waste_code_by_naf(self.naf_code)
        return self.render_to_response(self.get_context_data(naf_code=self.naf_code, department=self.department))


class NationalResult(SentinelEmailAccessMixin, FullyLoggedMixin, FormView):
    template_name = "sentinel/partials/_national_result.html"

    form_class = NafSearchForm
    naf_code = None

    def get(self, request, *args, **kwargs):
        raise Http404

    def form_valid(self, form):
        self.naf_code = form.cleaned_data.get("selected_naf_code")

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        national_graph = {}

        if self.naf_code:
            national_graph = build_national_graph(self.naf_code)

        return super().get_context_data(
            **kwargs,
            national_graph=national_graph,
            naf_code_label=get_naf_code_full_label(self.naf_code),
        )


class DepartmentResult(SentinelEmailAccessMixin, FullyLoggedMixin, FormView):
    template_name = "sentinel/partials/_department_result.html"

    form_class = NafSearchForm
    naf_code = None

    def get(self, request, *args, **kwargs):
        raise Http404

    def get_context_data(self, **kwargs):
        dept_graph = {}

        if self.naf_code:
            dept_graph = build_department_graph(self.naf_code, self.department)

        no_account_company_count = get_no_account_company_count(self.naf_code, self.department)

        with_account_company_count = get_with_account_company_count(self.naf_code, self.department)

        no_activity_company_count = get_no_activity_company_count(self.naf_code, self.department)

        with_activity_count = with_account_company_count - no_activity_company_count
        national_top_five = get_top_five_waste_code_by_naf(self.naf_code)
        return super().get_context_data(
            **kwargs,
            dept_graph=dept_graph,
            department=self.department,
            department_label=get_department_label(self.department),
            naf_code=self.naf_code,
            naf_code_label=get_naf_code_full_label(self.naf_code),
            national_top_five=national_top_five,
            with_account_company_count=with_account_company_count,
            no_account_company_count=no_account_company_count,
            with_activity_count=with_activity_count,
        )

    def form_valid(self, form):
        self.naf_code = form.cleaned_data.get("selected_naf_code")
        self.department = form.cleaned_data.get("department")

        return self.render_to_response(self.get_context_data())


class BaseResultTabs(SentinelEmailAccessMixin, FullyLoggedMixin, FormView):
    template_name = "sentinel/partials/_result_tabs.html"
    form_class = NafSearchForm
    extra_ctx = {}
    file_response = False

    def dispatch(self, request, *args, **kwargs):
        self.category = kwargs.get("category")
        if self.category not in [NON_REGISTERED, NO_ACTIVITY, ABNORMAL]:
            raise Http404("Invalid category")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        raise Http404

    def form_valid(self, form):
        self.naf_code = form.cleaned_data.get("selected_naf_code")
        self.department = form.cleaned_data.get("department")
        self.page = form.cleaned_data.get("page") or 1  # 1-based page index
        return self.build_response()

    def get_company_df(self):
        func = None
        func_kwargs = {"naf": self.naf_code, "department": self.department}  # sql pagination is 0 based index
        if not self.file_response:  # no pagination for file download
            func_kwargs["page"] = self.page - 1

        if self.category == NON_REGISTERED:
            func = get_company_not_on_td_list

        if self.category == NO_ACTIVITY:
            func = get_company_no_activity_list

        if self.category == ABNORMAL:
            func = get_company_abnormal_list
            national_stats_dicts = get_top_five_waste_code_by_naf(self.naf_code)

            waste_codes = [row["waste_code"] for row in national_stats_dicts]
            self.extra_ctx = {"top_waste_codes": waste_codes}
            func_kwargs.update({"waste_codes": waste_codes})

        df = func(**func_kwargs)

        return df


class ResultTabs(BaseResultTabs):
    """Partial table content for tabs"""

    template_name = "sentinel/partials/_result_tabs.html"

    def build_response(self):
        return self.render_to_response(self.get_context_data())

    def get_company_list(self):
        df = self.get_company_df()

        # df only contains current page rows, we fake the pagination
        total = self.get_company_totals()[self.category]
        data_list = ["" for _ in range(total)]
        paginator = Paginator(data_list, TAB_RESULT_PAGINATE_BY)
        page_obj = paginator.get_page(self.page)
        return {"companies": df.to_dicts(), "page_obj": page_obj}

    def get_company_totals(self):
        """Cache tab counts"""
        CACHE_DURATION = 60 * 0
        cache_key = f"total_{self.naf_code}_{self.department}"
        if cached := cache.get(cache_key):
            return cached
        res = {
            NON_REGISTERED: get_no_account_company_count(self.naf_code, self.department),
            NO_ACTIVITY: get_no_activity_company_count(self.naf_code, self.department),
            ABNORMAL: get_abnormal_company_count(self.naf_code, self.department),
        }
        cache.set(cache_key, res, CACHE_DURATION)
        return res

    def get_context_data(self, **kwargs):
        company_list = self.get_company_list()

        return super().get_context_data(
            **kwargs,
            tab_category=self.category,
            NON_REGISTERED=NON_REGISTERED,
            NO_ACTIVITY=NO_ACTIVITY,
            ABNORMAL=ABNORMAL,
            totals=self.get_company_totals(),
            department=self.department,
            naf_code=self.naf_code,
            page=self.page,
            companies=company_list["companies"],
            page_obj=company_list["page_obj"],
            **self.extra_ctx,
        )


class GenerateExcelView(BaseResultTabs):
    template_name = "dummy.html"
    file_response = True

    def build_response(self):
        return self.generate_excel_response(self.request)

    def generate_excel_response(self, request):
        """
        Generate Excel file from dataframe and return as HTTP response
        """
        try:
            df = self.get_company_df()

            excel_buffer = io.BytesIO()

            df.write_excel(excel_buffer, worksheet="Data")
            excel_buffer.seek(0)

            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            # Set filename for download
            filename = self.generate_filename()
            response["Content-Disposition"] = f'attachment; filename="{filename}"'

            return response

        except Exception as _:
            return HttpResponse("Erreur", status=400)

    def generate_filename(self):
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")

        return f"sentinelle_{self.category}_{timestamp}.xlsx"
