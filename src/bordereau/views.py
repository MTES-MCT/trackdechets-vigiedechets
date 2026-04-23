import json
import httpx
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import DetailView, FormView, TemplateView

from accounts.constants import PERMS_BSD_SEARCH
from common.mixins import FullyLoggedMixin

from .converters import BsdsToBsdsDisplaySearchResult
from .forms import BsdSearchForm, BsdAvancedSearchForm

from roadcontrol.models import BsdPdf

from .td_requests import (
    query_td_search_bsds,
    query_td_search_companies,
    query_td_forms,
)

class BsdSearch(FullyLoggedMixin, TemplateView):
    """
    Cette vue gère la recherche de BSD via l'API Trackdéchets. Elle affiche un formulaire de recherche qui peut être simple ou avancé en fonction des champs présents dans la requête POST, et affiche les résultats de la recherche.
    """
    template_name = "bordereau/bsd_search.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mode = self.request.GET.get("mode")
        siret = self.request.GET.get("siret")
        selected_company_json = self.request.GET.get("selected_company_json")

        if mode == "advanced":
            context["form"] = BsdAvancedSearchForm(initial={"siret": siret, "selected_company_json": selected_company_json})
            context["initial_form_template"] = "bordereau/partials/_advanced_search_form.html"
        else:
            context["form"] = BsdSearchForm(initial={"siret": siret, "selected_company_json": selected_company_json})
            context["initial_form_template"] = "bordereau/partials/_simple_search_form.html"
            
        return context

class BsdSimpleSearch(FullyLoggedMixin, TemplateView):
    """
    Cette vue renvoie uniquement le formulaire de recherche simple.
    """
    template_name = "bordereau/partials/_simple_search_form.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get_context_data(self, **kwargs):
        form = BsdSearchForm()
        return super().get_context_data(**kwargs, form=form)


class BsdAdvancedSearch(FullyLoggedMixin, TemplateView):
    """
    Cette vue renvoie uniquement le formulaire de recherche avancée.
    """
    template_name = "bordereau/partials/_advanced_search_form.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get_context_data(self, **kwargs):
        form = BsdAvancedSearchForm()
        return super().get_context_data(**kwargs, form=form)


class CompanySearchView(FullyLoggedMixin, TemplateView):
    """
    Cette vue gère la recherche d'entreprise via l'API Trackdéchets. Elle est utilisée pour alimenter les suggestions d'entreprise dans les formulaires de recherche.
    Elle prend en compte la recherche par SIRET, raison sociale ou numéro TVA, et peut également mettre en avant une entreprise sélectionnée précédemment grâce à un SIRET fourni dans la requête.
    """
    template_name = "bordereau/partials/_company_search_results.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get(self, request, *args, **kwargs):
        clue = (request.GET.get("search_clue_input") or request.GET.get("search_clue") or "").strip()
        selected_siret = request.GET.get("selected_siret")
        selected_company_json = request.GET.get("selected_company_json") # un champ optionnel qui peut contenir les données de l'entreprise sélectionnée au format JSON, pour éviter une requête supplémentaire à l'API si ces données sont déjà disponibles côté client

        # Si la recherche est inférieure à 3 caractères et qu'aucun SIRET sélectionné
        if len(clue) < 3 and not selected_siret:
            return HttpResponse("")

        # Si pas de recherche active mais un SIRET est sélectionné
        if len(clue) < 3 and selected_siret:
            # On récupére les infos de l'entreprise à partir du JSON fourni (cache client)
            if selected_company_json:
                return self.render_to_response({
                    "companies": [json.loads(selected_company_json)],
                    "selected_siret": selected_siret,
                    "toggle":False
                })

        # Recherche des entreprises via l'API Trackdéchets
        companies = query_td_search_companies(clue=clue)

        # Si un SIRET sélectionné est fourni, on tente de le mettre en avant dans les résultats
        if selected_siret:
            # On cherche l'entreprise correspondante dans les résultats de l'API
            selected_company = next((c for c in companies if c.get("siret") == selected_siret or c.get("vatNumber") == selected_siret), None)
            # Si on la trouve, on la met en premier dans la liste des résultats
            if selected_company:
                companies.remove(selected_company)
                companies.insert(0, selected_company)
            # Si on ne la trouve pas dans les résultats de l'API, on la récupére à partir du JSON fourni (cache client)
            else:
                companies.insert(0, json.loads(selected_company_json))

        return self.render_to_response({
            "companies": companies,
            "selected_siret": selected_siret,
            "toggle":True
        })


class BsdSearchResult(FullyLoggedMixin, FormView):
    success_url = ""
    template_name = "bordereau/partials/search_result_bsds.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get_form_class(self):
        """
        On choisit le formulaire à instancier en fonction des champs présents dans la requête POST.
        S'il y a des champs spécifiques à la recherche avancée, on instancie le formulaire de recherche avancée, sinon le formulaire de recherche simple.
        """
        if any(key in self.request.POST for key in ["code_dechet", "code_aiot", "start_date_rep", "end_date_rep", "start_date_exp", "end_date_exp"]):
            return BsdAvancedSearchForm
        return BsdSearchForm

    def form_valid(self, form):
        search_params = form.cleaned_data
        search_params.pop("search_clue") # on n'en a plus besoin(barre de recherche)
        query_name = "controlBsds" # ici il faut utiliser une autre query, mais l'API n'a pas implémentée une recherche comme celle ci  

        resp = query_td_forms(**search_params) # autre query avec juste **search_params une fois que l'API est prête

        nodes = []
        total_count = 0
        start_cursor = None
        end_cursor = None
        has_next_page = False
        has_previous_page = False

        if resp and "data" in resp and resp["data"].get(query_name):
            bsds = resp["data"][query_name]
            total_count = bsds["totalCount"]
            page_info = bsds["pageInfo"]
            start_cursor = page_info["startCursor"]
            end_cursor = page_info["endCursor"]
            has_next_page = page_info["hasNextPage"]
            has_previous_page = page_info["hasPreviousPage"]
            edges = bsds["edges"]
            nodes = [edge["node"] for edge in edges]

        converter = BsdsToBsdsDisplaySearchResult(nodes)
        converter.convert()

        bsds_ids = [{"bsd_id": bsd["id"], "readable_id": bsd["readable_id"]} for bsd in converter.bsds_display]

        return self.render_to_response(
            self.get_context_data(
                form=form,
                bsds=converter.bsds_display,
                bsds_ids=bsds_ids,
                search_params=search_params,
                total_count=total_count,
                start_cursor=start_cursor,
                end_cursor=end_cursor,
                has_next_page=has_next_page,
                has_previous_page=has_previous_page,
                bundle_download_available=False,
                request_type=BsdPdf.RequestTypeChoice.BSD,
            )
        )


class BsdRecentPdfs(FullyLoggedMixin, TemplateView):
    template_name = "bordereau/partials/_recent_pdfs.html"
    allowed_user_categories = PERMS_BSD_SEARCH

    def get_recent_downloads(self):
        user = self.request.user
        return BsdPdf.objects.bsd().filter(created_by=user)[:5]

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs, recent_downloads=self.get_recent_downloads(), download_column_name="N° de bordereau"
        )
