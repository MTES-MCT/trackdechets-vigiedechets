import json
import httpx
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import DetailView, FormView, TemplateView

from accounts.constants import PERMS_BSD_SEARCH
from common.mixins import FullyLoggedMixin

from .converters import BsdsToBsdsDisplaySearchResult
from .forms import BsdSearchForm

from roadcontrol.models import BsdPdf,PdfBundle 
from bordereau.tasks import prepare_bordereau_bundle

from .td_requests import (
    query_td_bordereaux_search,
    query_td_search_companies,
)

from celery.result import AsyncResult
from config.celery_app import app
from common.constants import STATE_DONE, STATE_RUNNING



class BsdSearch(FullyLoggedMixin, TemplateView):
    template_name = "bordereau/bordereau_search.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        siret = self.request.GET.get("siret")
        selected_company_json = self.request.GET.get("selected_company_json")
        context["form"] = BsdSearchForm(
            initial={"siret": siret, "selected_company_json": selected_company_json}
        )
        context["recent_downloads"] = BsdPdf.objects.bsd().filter(created_by=self.request.user)[:5]
        context["download_column_name"] = "N° de bordereau"
        return context


class CompanySearchView(FullyLoggedMixin, TemplateView):
    template_name = "bordereau/partials/_company_search_results.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get(self, request, *args, **kwargs):
        clue = request.GET.get("search_clue", "").strip()
        department = request.GET.get("code_postal", "").strip() or None
        selected_siret = request.GET.get("selected_siret")
        selected_company_json = request.GET.get("selected_company_json")

        if len(clue) < 3 and not selected_siret:
            return HttpResponse("")

        if len(clue) < 3 and selected_siret:
            if selected_company_json:
                return self.render_to_response({
                    "companies": [json.loads(selected_company_json)],
                    "selected_siret": selected_siret,
                    "toggle": False,
                })

        companies = query_td_search_companies(clue=clue, department=department)

        if selected_siret:
            selected_company = next(
                (c for c in companies if c.get("siret") == selected_siret or c.get("vatNumber") == selected_siret),
                None
            )
            if selected_company:
                companies.remove(selected_company)
                companies.insert(0, selected_company)
            elif selected_company_json:
                companies.insert(0, json.loads(selected_company_json))

        return self.render_to_response({
            "companies": companies,
            "selected_siret": selected_siret,
            "toggle": True,
        })


class BsdSearchResultById(FullyLoggedMixin, FormView):
    success_url = ""
    template_name = "bordereau/partials/search_result_bsds_by_id.html"
    allowed_user_categories = PERMS_BSD_SEARCH
    form_class = BsdSearchForm

    def form_valid(self, form):
        cursors_history_str = self.request.POST.get("cursors_history", "")
        cursors = cursors_history_str.split(",") if cursors_history_str else []
        current_page = int(self.request.POST.get("current_page", 1))
        page_size = 10

        search_params = form.cleaned_data.copy()
        bsd_id_searched = search_params.get("bsd_id", "")

        search_params.pop("search_clue", None)
        search_params.pop("code_postal", None)
        search_params.pop("search_by_company", None)
        
        fetch_cursor = cursors[-1] if cursors else None

        resp = query_td_bordereaux_search(
            **search_params, end_cursor=fetch_cursor, page_size=page_size
        )

        nodes = []
        total_count = 0
        has_next_page = False
        has_previous_page = False
        start_cursor = None
        end_cursor = None
        next_page = current_page
        prev_page = current_page

        query_name = "bordereauxSearch"
        if resp and resp.get("data") is not None and resp["data"].get(query_name):
            bsds_resp = resp["data"][query_name]
            total_count = bsds_resp["totalCount"]
            page_info = bsds_resp["pageInfo"]
            start_cursor = page_info["startCursor"]
            end_cursor = page_info["endCursor"]
            
            next_cursors = cursors + [end_cursor] if end_cursor else cursors
            next_cursors_str = ",".join(next_cursors)
            
            prev_cursors = cursors[:-1] if cursors else []
            prev_cursors_str = ",".join(prev_cursors)
            
            has_next_page = page_info["hasNextPage"]
            has_previous_page = current_page > 1
            next_page = current_page + 1 if has_next_page else current_page
            prev_page = current_page - 1 if has_previous_page else current_page
            nodes = [edge["node"] for edge in bsds_resp["edges"]]

        converter = BsdsToBsdsDisplaySearchResult(nodes)
        converter.convert()

        bsds_ids = [
            {"bsd_id": bsd["id"], "readable_id": bsd["readable_id"]}
            for bsd in converter.bsds_display
        ]

        custom_error_message = None
        if total_count == 0:
            custom_error_message = f"Aucun bordereau n’a été trouvé avec le numéro {bsd_id_searched}"

        return self.render_to_response(
            self.get_context_data(
                form=form,
                bsds=converter.bsds_display,
                bsds_ids=bsds_ids,
                search_params=search_params,
                total_count=total_count,
                start_cursor=start_cursor,
                end_cursor=end_cursor,
                next_cursors_str=next_cursors_str,
                prev_cursors_str=prev_cursors_str,
                has_next_page=has_next_page,
                has_previous_page=has_previous_page,
                bundle_download_available=True,
                request_type=BsdPdf.RequestTypeChoice.BSD,
                current_page=current_page,
                next_page=next_page,
                prev_page=prev_page,
                page_size=page_size,
                total_pages=max(1, -(-total_count // page_size)),
                custom_error_message=custom_error_message,  # 👈 Envoyé au HTML
            )
        )

class BsdSearchResult(FullyLoggedMixin, FormView):
    success_url = ""
    template_name = "bordereau/partials/search_result_bsds.html"
    allowed_user_categories = PERMS_BSD_SEARCH
    form_class = BsdSearchForm

    def form_valid(self, form):
        cursors_history_str = self.request.POST.get("cursors_history", "")
        cursors = cursors_history_str.split(",") if cursors_history_str else []
        current_page = int(self.request.POST.get("current_page", 1))
        page_size = 10

        search_params = form.cleaned_data.copy()
        search_params.pop("search_clue", None)
        search_params.pop("code_postal", None)
        search_by_company = search_params.pop("search_by_company", None)
        
        fetch_cursor = cursors[-1] if cursors else None

        print("search params:", search_params)

        resp = query_td_bordereaux_search(
            **search_params, end_cursor=fetch_cursor, page_size=page_size
        )

        nodes = []
        total_count = 0
        has_next_page = False
        has_previous_page = False
        start_cursor = None
        end_cursor = None
        next_page = current_page
        prev_page = current_page

        query_name = "bordereauxSearch"
        if resp and "data" in resp and resp["data"].get(query_name):
            bsds_resp = resp["data"][query_name]
            total_count = bsds_resp["totalCount"]
            page_info = bsds_resp["pageInfo"]
            start_cursor = page_info["startCursor"]
            end_cursor = page_info["endCursor"]
            
            next_cursors = cursors + [end_cursor] if end_cursor else cursors
            next_cursors_str = ",".join(next_cursors)
            
            prev_cursors = cursors[:-1] if cursors else []
            prev_cursors_str = ",".join(prev_cursors)
            
            has_next_page = page_info["hasNextPage"]
            has_previous_page = current_page > 1
            next_page = current_page + 1 if has_next_page else current_page
            prev_page = current_page - 1 if has_previous_page else current_page
            nodes = [edge["node"] for edge in bsds_resp["edges"]]

        converter = BsdsToBsdsDisplaySearchResult(nodes)
        converter.convert()

        bsds_ids = [
            {"bsd_id": bsd["id"], "readable_id": bsd["readable_id"]}
            for bsd in converter.bsds_display
        ]

        #print(bsd_display := converter.bsds_display)  # Debug: affiche les données converties pour vérification

        return self.render_to_response(
            self.get_context_data(
                form=form,
                bsds=converter.bsds_display,
                bsds_ids=bsds_ids,
                search_params={**search_params, "search_by_company": search_by_company},  # ← réinjecté
                total_count=total_count,
                start_cursor=start_cursor,
                end_cursor=end_cursor,
                next_cursors_str=next_cursors_str,
                prev_cursors_str=prev_cursors_str,
                has_next_page=has_next_page,
                has_previous_page=has_previous_page,
                bundle_download_available=True,
                request_type=BsdPdf.RequestTypeChoice.BSD,
                current_page=current_page,
                next_page=next_page,
                prev_page=prev_page,
                page_size=page_size,
                total_pages=max(1, -(-total_count // page_size)),
            )
        )


class BsdRecentSearch(FullyLoggedMixin, TemplateView):
    template_name = "bordereau/partials/_recent_pdfs.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get_recent_downloads(self):
        user = self.request.user
        bundles = PdfBundle.objects.bsd().ready().filter(created_by=user)[:5]
        pdfs = BsdPdf.objects.bsd().filter(bundle=None, created_by=user)[:5]

        return sorted(list(bundles) + list(pdfs), key=lambda i: getattr(i, "created_at"), reverse=True)[:5]

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs, 
            recent_downloads=self.get_recent_downloads()
        )

class BsdPdfBundle(FullyLoggedMixin, TemplateView):
    template_name = "dummy.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def post(self, request, *args, **kwargs):
        # 1. Extraction et formatage des critères textuels pour le cadre du PDF
        siret_searched = request.POST.get("siret") or "Tous"
        bsd_id_searched = request.POST.get("bsd_id") or "Tous"
        codes_dechet_searched = ", ".join(request.POST.getlist("code_dechet")) or "Tous"
        code_aiot_searched = request.POST.get("code_aiot") or "Tous"
        
        start_rep = request.POST.get("start_date_rep")
        end_rep = request.POST.get("end_date_rep")
        dates_reception = f"Du {start_rep} au {end_rep}" if (start_rep or end_rep) else "Toutes dates"
        
        start_exp = request.POST.get("start_date_exp")
        end_exp = request.POST.get("end_date_exp")
        dates_expedition = f"Du {start_exp} au {end_exp}" if (start_exp or end_exp) else "Toutes dates"

        # 2. Préparation des paramètres de recherche pour requêter l'API Trackdéchets
        search_params = {
            "siret": request.POST.get("siret"),
            "bsd_id": request.POST.get("bsd_id"),
            "search_by_company": request.POST.get("search_by_company") == "true",
            "code_dechet": request.POST.getlist("code_dechet"),
            "code_aiot": request.POST.getlist("code_aiot"),
            "start_date_rep": request.POST.get("start_date_rep"),
            "end_date_rep": request.POST.get("end_date_rep"),
            "start_date_exp": request.POST.get("start_date_exp"),
            "end_date_exp": request.POST.get("end_date_exp"),
        }
        
        search_params = {k: v for k, v in search_params.items() if v}
        search_params.pop("search_by_company", None)

        resp = query_td_bordereaux_search(**search_params, page_size=100)
        
        nodes = []
        if resp and resp.get("data") and resp["data"].get("bordereauxSearch"):
            nodes = [edge["node"] for edge in resp["data"]["bordereauxSearch"]["edges"]]

        converter = BsdsToBsdsDisplaySearchResult(nodes)
        converter.convert()
        
        bundle_params = [
            {
                "bsd_type": bsd.get("bsd_type"),
                "bsd_id": bsd.get("id"),
                "readable_id": bsd.get("readable_id"),
                "waste_code": bsd.get("waste_details", {}).get("code") or "",
                "weight": bsd.get("waste_details", {}).get("weight") or "0",
                "adr_code": bsd.get("adr") or "",
                "packagings": bsd.get("packagings") or "",
            }
            for bsd in converter.bsds_display
        ]

        # 3. Association des critères de recherche aux attributs du modèle PdfBundle
        bundle = PdfBundle.objects.create(
            created_by=request.user,
            company_siret=siret_searched,          # Devient N° SIRET
            transporter_plate=bsd_id_searched,      # Devient N° de bordereau
            company_name=codes_dechet_searched,     # Devient Codes Déchets
            company_address=code_aiot_searched,     # Devient Code MonAIOT
            company_contact=dates_reception,        # Devient Dates de réception
            company_email=dates_expedition,         # Devient Dates d'expédition
            params=bundle_params,
            request_type=BsdPdf.RequestTypeChoice.BSD,
        )

        task = prepare_bordereau_bundle.delay(bundle.pk)

        return redirect("bordereau_pdf_bundle_processing", task_id=task.id, bundle_pk=str(bundle.pk))


class BsdBundleProcessingView(FullyLoggedMixin, TemplateView):
    template_name = "bordereau/bundle_processing.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "task_id": self.kwargs.get("task_id", None),
            "bundle_pk": self.kwargs.get("bundle_pk", None),
        })
        return ctx


class BsdFragmentBundleProcessingView(FullyLoggedMixin, TemplateView):
    template_name = "bordereau/partials/_prepare_bundle.html"
    allowed_user_categories = PERMS_BSD_SEARCH

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
            custom_message = f"{progress} % : {bsds_count}/{bsds_total_count} bordereaux"
            
        ctx.update({"custom_message": custom_message})

        if not job.ready():
            ctx.update({"state": STATE_RUNNING})
        else:
            result = job.get() if job.successful() else {}
            ctx.update({
                "errors": result.get("errors", []),
                "state": STATE_DONE,
                "redirect_to": result.get("redirect", ""),
            })
        return ctx


class BsdPdfBundleResult(FullyLoggedMixin, DetailView):
    model = PdfBundle
    context_object_name = "bundle"
    template_name = "bordereau/bundle_result.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get_queryset(self):
        return super().get_queryset().filter(created_by=self.request.user)