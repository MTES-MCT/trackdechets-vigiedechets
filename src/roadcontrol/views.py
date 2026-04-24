import httpx
from celery.result import AsyncResult
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic import DetailView, FormView, TemplateView

from accounts.constants import PERMS_BSD_SEARCH, PERMS_ROAD_CONTROL
from common.constants import STATE_DONE, STATE_RUNNING
from common.mixins import FullyLoggedMixin
from config.celery_app import app

from .converters import BsdsToBsdsDisplay
from .exceptions import FormDownloadException
from .forms import RoadControlSearchForm
from .helpers import get_company_data
from .models import BsdPdf, PdfBundle
from .rendering_helpers import render_pdf
from .task import prepare_bundle
from .td_requests import (
    query_td_control_bsds,
    query_td_pdf,
)


class RoadControlSearch(FullyLoggedMixin, TemplateView):
    template_name = "roadcontrol/roadcontrol.html"
    allowed_user_categories = PERMS_ROAD_CONTROL

    def get_context_data(self, **kwargs):
        form = RoadControlSearchForm()
        return super().get_context_data(**kwargs, form=form)


class RoadControlSearchResult(FullyLoggedMixin, FormView):
    form_class = RoadControlSearchForm
    success_url = ""
    template_name = "roadcontrol/partials/search_result.html"
    allowed_user_categories = PERMS_ROAD_CONTROL

    def form_valid(self, form):
        siret = form.cleaned_data["siret"]
        plate = form.cleaned_data["plate"]

        form_end_cursor = form.cleaned_data.get("end_cursor", None)

        query_name = "controlBsds"
        resp = query_td_control_bsds(siret=siret, plate=plate, end_cursor=form_end_cursor)

        nodes = []
        total_count = 0

        start_cursor = None
        end_cursor = None
        has_next_page = False
        has_previous_page = False
        if resp:
            bsds = resp["data"][query_name]
            total_count = bsds["totalCount"]
            page_info = bsds["pageInfo"]
            start_cursor = page_info["startCursor"]
            end_cursor = page_info["endCursor"]

            has_next_page = page_info["hasNextPage"]
            # has_previous_page = page_info["has_previous_page"]  bsds api is currently buggy on hasNextPage
            has_previous_page = bool(form_end_cursor)
            edges = bsds["edges"]

            nodes = [edge["node"] for edge in edges]

        converter = BsdsToBsdsDisplay(nodes)
        converter.convert()

        bsds_ids = [{"bsd_id": bsd["id"], "readable_id": bsd["readable_id"]} for bsd in converter.bsds_display]

        search_params = {"plate": plate, "siret": siret}
        return self.render_to_response(
            self.get_context_data(
                form=form,
                bsds=converter.bsds_display,
                bsds_ids=bsds_ids,
                search_params=search_params,
                total_count=total_count,
                no_bsd_found_pdf_available=not total_count,
                start_cursor=start_cursor,
                end_cursor=end_cursor,
                has_next_page=has_next_page,
                has_previous_page=has_previous_page,
                bundle_download_available=True,
                request_type=BsdPdf.RequestTypeChoice.ROAD_CONTROL,
            )
        )


class BsdRetrievingMixin:
    def get_search_params(self, request):
        siret = request.POST.get("siret")
        plate = request.POST.get("plate")
        adr = request.POST.get("adr")

        return {"siret": siret, "plate": plate, "adr": adr}

    def get_bsd_data(self, request):
        adr_code = request.POST.get("adr_code", "")
        waste_code = request.POST.get("waste_code", "")
        weight = request.POST.get("weight", "0")
        packagings = request.POST.get("packagings", "")
        return {"adr_code": adr_code, "waste_code": waste_code, "weight": weight, "packagings": packagings}


class NoResultRoadControlPdf(FullyLoggedMixin, BsdRetrievingMixin, FormView):
    template_name = "roadcontrol/pdf/no_result_road_control_pdf.html"
    form_class = RoadControlSearchForm
    http_method_names = ["post"]
    success_url = ""
    allowed_user_categories = PERMS_ROAD_CONTROL

    def form_valid(self, form):
        company_data = {}
        siret = form.cleaned_data["siret"]
        plate = form.cleaned_data["plate"]

        if siret:
            company_data = get_company_data(siret)

        ctx = {
            "bundle": {
                **company_data,
                "company_siret": siret,
                "transporter_plate": plate,
                "created_at": timezone.now(),
            }
        }
        content = render_to_string(self.template_name, ctx)

        pdf = render_pdf(content)

        response = HttpResponse(content_type="application/pdf")
        now = timezone.now()
        response["Content-Disposition"] = f'attachment; filename="Contrôle routier {now:%d-%m-%Y %H%M}.pdf"'
        response.write(pdf)

        return response


class SingleBsdPdfDownload(FullyLoggedMixin, BsdRetrievingMixin, TemplateView):
    """Pdf download view used by control and bsd views"""

    template_name = "roadcontrol/road_control_pdf.html"
    allowed_user_categories = list({*PERMS_ROAD_CONTROL, *PERMS_BSD_SEARCH})

    def get_pdf_download_link(self, bsd_type, bsd_id):
        link = query_td_pdf(bsd_type=bsd_type, bsd_id=bsd_id)

        return link

    def get_pdf_download_content(self, link):
        try:
            r = self.client.get(link)
        except httpx.RequestError:
            raise FormDownloadException()
        return r.content

    def post(self, request, *args, **kwargs):
        bsd_id = request.POST.get("bsd_id")
        bsd_type = request.POST.get("bsd_type")
        bsd_readable_id = request.POST.get("bsd_readable_id", None) or bsd_id
        request_type = request.POST.get("request_type", BsdPdf.RequestTypeChoice.ROAD_CONTROL)

        search_params = self.get_search_params(request)
        siret = search_params["siret"]
        plate = search_params["plate"]
        company_data = get_company_data(siret) if siret else {}
        bsd_data = self.get_bsd_data(request)

        self.client = httpx.Client(timeout=60)  # 60 seconds
        download_link = self.get_pdf_download_link(bsd_type=bsd_type, bsd_id=bsd_id)

        pdfdata = self.get_pdf_download_content(download_link)

        file = ContentFile(pdfdata, name="bsd.pdf")

        bsd_pdf = BsdPdf.objects.create(
            bsd_id=bsd_readable_id,
            pdf_file=file,
            company_siret=siret,
            transporter_plate=plate,
            **company_data,
            **bsd_data,
            created_by=request.user,
            request_type=request_type,
        )

        res = self.render_to_response(context={"bsd_pdf": bsd_pdf})
        res["HX-Trigger"] = "reloadRecentPdfs"
        return res


class RoadControlPdfBundle(FullyLoggedMixin, BsdRetrievingMixin, TemplateView):
    template_name = "dummy.html"
    allowed_user_categories = PERMS_ROAD_CONTROL

    def post(self, request, *args, **kwargs):
        bsd_ids = request.POST.getlist("bsd_ids[]")
        bsd_types = request.POST.getlist("bsd_types[]")
        readable_ids = request.POST.getlist("readable_ids[]")
        waste_codes = request.POST.getlist("waste_codes[]")
        weights = request.POST.getlist("weights[]")
        adr_codes = request.POST.getlist("adr_codes[]")
        packagings = request.POST.getlist("packagings[]")

        search_params = self.get_search_params(request)
        siret = search_params.get("siret", "")
        plate = search_params.get("plate", "")
        company_data = get_company_data(siret)
        bundle = PdfBundle.objects.create(
            created_by=request.user,
            company_siret=siret,
            transporter_plate=plate,
            **company_data,
            params=[
                {
                    "bsd_type": bsd_type,
                    "bsd_id": bsd_id,
                    "readable_id": readable_id,
                    "waste_code": waste_code,
                    "weight": weight,
                    "adr_code": adr_code,
                    "packagings": packaging,
                }
                for bsd_type, bsd_id, readable_id, waste_code, weight, adr_code, packaging in zip(
                    bsd_types, bsd_ids, readable_ids, waste_codes, weights, adr_codes, packagings
                )
            ],
        )

        task = prepare_bundle.delay(bundle.pk)

        return redirect("roadcontrol_pdf_bundle_processing", task_id=task.id, bundle_pk=str(bundle.pk))


class BundleProcessingView(FullyLoggedMixin, TemplateView):
    template_name = "roadcontrol/bundle_processing.html"
    allowed_user_categories = PERMS_ROAD_CONTROL

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "task_id": self.kwargs.get("task_id", None),
                "bundle_pk": self.kwargs.get("bundle_pk", None),
            }
        )
        return ctx


class FragmentBundleProcessingView(FullyLoggedMixin, TemplateView):
    template_name = "roadcontrol/partials/_prepare_bundle.html"
    allowed_user_categories = PERMS_ROAD_CONTROL

    def dispatch(self, request, *args, **kwargs):
        self.task_id = self.kwargs.get("task_id")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        job = AsyncResult(self.task_id, app=app)
        done = job.ready()
        result = job.result
        bsds_count = "N/A"
        bsds_total_count = "N/A"
        if isinstance(result, dict):
            progress = result.get("progress", 0)
            bsds_count = result.get("bsds_count", 0)
            bsds_total_count = result.get("bsds_total_count", 0)

        else:
            progress = 100.0 if done else 0.0
        custom_message = "Préparation en cours"
        if bsds_count and bsds_total_count:
            custom_message = f"{progress} % : {bsds_count}/{bsds_total_count} bsds"
        ctx.update({"custom_message": custom_message})

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


class RoadControlPdfBundleResult(FullyLoggedMixin, DetailView):
    model = PdfBundle
    context_object_name = "bundle"
    template_name = "roadcontrol/bundle_result.html"
    allowed_user_categories = PERMS_ROAD_CONTROL

    def get_queryset(self):
        return super().get_queryset().filter(created_by=self.request.user)


class RoadControlRecentPdfs(FullyLoggedMixin, TemplateView):
    template_name = "roadcontrol/partials/_recent_pdfs.html"
    allowed_user_categories = PERMS_ROAD_CONTROL

    def get_recent_downloads(self):
        user = self.request.user
        bundles = PdfBundle.objects.ready().filter(created_by=user)[:5]
        pdfs = BsdPdf.objects.road_control().filter(bundle=None, created_by=user)[:5]

        return sorted(list(bundles) + list(pdfs), key=lambda i: getattr(i, "created_at"), reverse=True)[:5]

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs, recent_downloads=self.get_recent_downloads(), download_column_name="N° de bordereau/dossier"
        )