import base64
import datetime as dt

from celery.result import AsyncResult
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, TemplateView

from accounts.constants import PERMS_SHEET_AND_REGISTRY
from common.constants import STATE_DONE, STATE_RUNNING
from common.mixins import FullyLoggedMixin
from common.sirets import validate_siret
from config.celery_app import app

from ..forms import SheetPrepareForm
from ..models import ComputedInspectionData
from ..task import prepare_sheet, render_pdf

CHECK_INSPECTION = False


class SheetPrepare(FullyLoggedMixin, FormView):
    """
    View to prepare an inspection sheet $:
        - render a form
        - launch an async task
        - redirect to a self refreshing waiting page
    """

    template_name = "sheets/sheet_prepare.html"
    form_class = SheetPrepareForm
    allowed_user_categories = PERMS_SHEET_AND_REGISTRY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.existing_inspection = None
        self.new_inspection = None

    def check_existing_inspection(self, siret):
        if not CHECK_INSPECTION:
            self.existing_inspection = None
            return
        today = dt.date.today()
        self.existing_inspection = ComputedInspectionData.objects.filter(org_id=siret, created__date=today).first()

    def get_initial(self):
        # prefill siret field when coming from map
        siret = self.request.GET.get("siret", "")
        init = super().get_initial()
        if validate_siret(siret):
            init["siret"] = siret
        return init

    def form_valid(self, form):
        return self.handle_inspection(form)

    def handle_inspection(self, form):
        siret = form.cleaned_data["siret"]
        data_start_date = form.cleaned_data["start_date"]
        data_end_date = form.cleaned_data["end_date"]
        if self.existing_inspection:
            return super().form_valid(form)

        self.new_inspection = ComputedInspectionData.objects.create(
            org_id=siret,
            data_start_date=data_start_date,
            data_end_date=data_end_date,
            created_by=self.request.user.email,
        )
        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
            self.task_id = "fake-task-id"
        else:
            self.task_id = prepare_sheet.delay(self.new_inspection.pk)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        year = dt.date.today().year
        label_this_year = year
        label_prev_year = year - 1
        return super().get_context_data(
            **kwargs, computed=self.new_inspection, label_this_year=label_this_year, label_prev_year=label_prev_year
        )

    def get_success_url(self):
        if self.existing_inspection:
            return reverse("sheet", args=[self.existing_inspection.pk])
        return reverse(
            "pollable_result",
            kwargs={"compute_pk": self.new_inspection.pk, "task_id": self.task_id},
        )


class ComputingView(FullyLoggedMixin, TemplateView):
    """Optional `task_id` trigger result polling in template"""

    template_name = "sheets/result.html"
    allowed_user_categories = PERMS_SHEET_AND_REGISTRY

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "task_id": self.kwargs.get("task_id", None),
                "compute_pk": self.kwargs.get("compute_pk", None),
                "redirect_to": "html",
            }
        )
        return ctx


class RenderingView(ComputingView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "redirect_to": "pdf",
            }
        )
        return ctx


class FragmentResultView(FullyLoggedMixin, TemplateView):
    """View to be called by ResultView template to render api call results when done"""

    template_name = "sheets/_prepare_result.html"
    allowed_user_categories = PERMS_SHEET_AND_REGISTRY

    def dispatch(self, request, *args, **kwargs):
        self.task_id = self.kwargs.get("task_id")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        job = AsyncResult(self.task_id, app=app)
        done = job.ready()
        result = job.result

        if isinstance(result, dict):
            progress = result.get("progress", 0)

        else:
            progress = 100.0 if done else 0.0

        ctx.update({"progress": int(progress)})

        if not job.ready():
            ctx.update({"state": STATE_RUNNING})
        else:
            result = job.get()
            ctx.update(
                {
                    "errors": result.get("errors", []),
                    "state": STATE_DONE,
                    "redirect_to": result.get("redirect", ""),
                }
            )
        return ctx


class Sheet(FullyLoggedMixin, DetailView):
    model = ComputedInspectionData
    template_name = "sheets/sheet.html"
    context_object_name = "sheet"
    allowed_user_categories = PERMS_SHEET_AND_REGISTRY


class PrepareSheetPdf(FullyLoggedMixin, DetailView):
    model = ComputedInspectionData
    allowed_user_categories = PERMS_SHEET_AND_REGISTRY

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.is_graph_rendered:
            return HttpResponseRedirect(reverse("sheet_pdf", args=[self.object.pk]))
        if self.object.is_computed:
            task = render_pdf.delay(self.object.pk)
            return HttpResponseRedirect(
                reverse(
                    "pollable_result_pdf",
                    kwargs={"compute_pk": self.object.pk, "task_id": task.id},
                )
            )
        return HttpResponseRedirect("/")


class SheetPdfHtml(FullyLoggedMixin, DetailView):
    """For debugging purpose"""

    model = ComputedInspectionData
    template_name = "sheets/sheetpdf.html"
    context_object_name = "sheet"
    allowed_user_categories = PERMS_SHEET_AND_REGISTRY

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()

        # todo: useless, remove
        ctx.update(
            {
                "bsdd_created_rectified_graph": self.object.bsdd_created_rectified_graph,
                "bsdd_stock_graph": self.object.bsdd_stock_graph,
                "bsdd_non_dangerous_created_rectified_graph": self.object.bsdd_non_dangerous_created_rectified_graph,
                "bsdd_non_dangerous_stock_graph": self.object.bsdd_non_dangerous_stock_graph,
                "bsda_created_rectified_graph": self.object.bsda_created_rectified_graph,
                "bsda_stock_graph": self.object.bsda_stock_graph,
                "bsdasri_created_rectified_graph": self.object.bsdasri_created_rectified_graph,
                "bsdasri_stock_graph": self.object.bsdasri_stock_graph,
                "bsff_created_rectified_graph": self.object.bsff_created_rectified_graph,
                "bsff_stock_graph": self.object.bsff_stock_graph,
                "bsvhu_created_rectified_graph": self.object.bsvhu_created_rectified_graph,
                "bsvhu_stock_graph": self.object.bsvhu_stock_graph,
                "waste_origin_graph": self.object.waste_origin_graph,
                "icpe_2770_graph": self.object.icpe_2770_graph,
                "icpe_2790_graph": self.object.icpe_2790_graph,
                "icpe_2760_1_graph": self.object.icpe_2760_1_graph,
                "icpe_2771_graph": self.object.icpe_2771_graph,
                "icpe_2791_graph": self.object.icpe_2791_graph,
                "icpe_2760_2_graph": self.object.icpe_2760_2_graph,
                "bsda_worker_quantity_graph": self.object.bsda_worker_quantity_graph,
                "transporter_bordereaux_stats_graph": self.object.transporter_bordereaux_stats_graph,
                "quantities_transported_stats_graph": self.object.quantities_transported_stats_graph,
                "non_dangerous_waste_statements_graph": self.object.non_dangerous_waste_statements_graph,
                "non_dangerous_waste_quantities_graph": self.object.non_dangerous_waste_quantities_graph,
            }
        )
        return ctx


class SheetPdf(FullyLoggedMixin, DetailView):
    model = ComputedInspectionData
    allowed_user_categories = PERMS_SHEET_AND_REGISTRY

    def get(self, request, *args, **kwargs):
        sheet = self.get_object()
        # todo: check state
        decoded = base64.b64decode(sheet.pdf)

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{sheet.pdf_filename}.pdf"'
        response.write(decoded)
        return response
