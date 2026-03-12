import datetime as dt
import io
import zipfile
from concurrent.futures import ThreadPoolExecutor

import httpx
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import CreateView, FormView, ListView
from rest_framework.reverse import reverse_lazy

from accounts.constants import PERMS_SHEET_AND_REGISTRY
from common.constants import HISTORY_SIZE
from common.mixins import FullyLoggedMixin
from data_exports.views import DummyForm

from .constants import RegistryV2DeclarationType, RegistryV2ExportState, RegistryV2ExportType
from .forms import RegistryV2PrepareForm
from .gql import graphql_registry_V2_export_download_signed_url
from .models import RegistryV2Export, RegistryV2ExportSiren
from .task import process_export


class RegistryDownloadException(Exception):
    def __init__(self, message="Erreur de téléchargement"):
        self.message = message
        super().__init__(self.message)


class RegistryV2Prepare(FullyLoggedMixin, CreateView):
    """
    View to download a registry
    """

    template_name = "registry/registry_v2_prepare.html"
    form_class = RegistryV2PrepareForm
    allowed_user_categories = PERMS_SHEET_AND_REGISTRY
    success_url = reverse_lazy("registry_v2_prepare")

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["created_by"] = self.request.user
        return kw

    def get_context_data(self, **kwargs):
        year = dt.date.today().year
        label_this_year = year
        label_prev_year = year - 1
        return super().get_context_data(**kwargs, label_this_year=label_this_year, label_prev_year=label_prev_year)

    def form_valid(
        self,
        form,
    ):
        res = super().form_valid(form)

        process_export(self.object.pk)
        return res


class RegistryV2ListContent(FullyLoggedMixin, ListView):
    """List exports - shows both SIRET and SIREN exports"""

    template_name = "registry/fragments/_registry_v2_list_content.html"
    allowed_user_categories = PERMS_SHEET_AND_REGISTRY
    context_object_name = "exports"

    def get_queryset(self):
        """Get both SIRET and SIREN exports, combine and sort by created_at"""
        # Get SIRET exports
        siret_exports = RegistryV2Export.objects.filter(created_by=self.request.user).values(
            "id",
            "siret",
            "state",
            "created_at",
            "export_format",
            "registry_type",
            "declaration_type",
            "start_date",
            "end_date",
        )

        # Get SIREN exports
        siren_exports = RegistryV2ExportSiren.objects.filter(created_by=self.request.user).values(
            "id",
            "siren",
            "state",
            "created_at",
            "export_format",
            "registry_type",
            "declaration_type",
            "start_date",
            "end_date",
            "total_sirets",
            "completed_sirets",
        )

        # Create lookup dictionaries for display labels
        registry_type_labels = {choice[0]: choice[1] for choice in RegistryV2ExportType.choices}
        declaration_type_labels = {choice[0]: choice[1] for choice in RegistryV2DeclarationType.choices}

        # Combine and mark with type indicator
        combined = []
        for export in siret_exports:
            export["type"] = "SIRET"
            export["identifier"] = export["siret"]
            export["registry_type_display"] = registry_type_labels.get(
                export["registry_type"], export["registry_type"]
            )
            export["declaration_type_display"] = declaration_type_labels.get(
                export["declaration_type"], export["declaration_type"]
            )
            combined.append(export)

        for export in siren_exports:
            export["type"] = "SIREN"
            export["identifier"] = export["siren"]
            export["registry_type_display"] = registry_type_labels.get(
                export["registry_type"], export["registry_type"]
            )
            export["declaration_type_display"] = declaration_type_labels.get(
                export["declaration_type"], export["declaration_type"]
            )
            combined.append(export)

        # Sort by created_at descending and limit to HISTORY_SIZE
        combined.sort(key=lambda x: x["created_at"], reverse=True)
        return combined[:HISTORY_SIZE]


class RegistryV2Retrieve(FullyLoggedMixin, FormView):
    """Download export - handles both SIRET and SIREN exports"""

    template_name = "registry/fragments/_registry_v2_list_content.html"
    form_class = DummyForm
    success_url = None
    allowed_user_categories = PERMS_SHEET_AND_REGISTRY

    def form_valid(self, form):
        registry_pk = self.kwargs.get("registry_pk")

        # Try SIREN export first
        try:
            siren_export = RegistryV2ExportSiren.objects.get(pk=registry_pk, created_by=self.request.user)
            return self._handle_siren_download(siren_export)
        except RegistryV2ExportSiren.DoesNotExist:
            pass

        # Fallback to SIRET export
        try:
            export = RegistryV2Export.objects.get(pk=registry_pk, created_by=self.request.user)
            return self._handle_siret_download(export)
        except RegistryV2Export.DoesNotExist:
            messages.error(self.request, "Export introuvable")
            return HttpResponseRedirect(reverse_lazy("registry_v2_prepare"))

    def _fetch_file(self, siret_export):
        """Returns (siret, bytes) or None on failure."""
        url = self._fetch_signed_url(siret_export.registry_export_id)
        if url is None:
            return None
        try:
            response = httpx.get(url, timeout=60, follow_redirects=True)
            response.raise_for_status()
            return (siret_export.siret, response.content)
        except Exception:
            return None

    def _handle_siren_download(self, siren_export):
        """Handle download for SIREN export — returns a ZIP of all completed SIRET exports."""
        completed_exports = list(siren_export.siret_exports.filter(state=RegistryV2ExportState.SUCCESSFUL))

        if not completed_exports:
            messages.error(
                self.request,
                f"Aucun export disponible ({siren_export.completed_sirets}/{siren_export.total_sirets} terminés)",
            )
            return HttpResponseRedirect(reverse_lazy("registry_v2_prepare"))

        ext = siren_export.export_format.lower()  # "csv" or "xlsx"

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(self._fetch_file, completed_exports))

        files = [r for r in results if r is not None]
        if not files:
            messages.error(self.request, "Erreur lors du téléchargement des exports")
            return HttpResponseRedirect(reverse_lazy("registry_v2_prepare"))

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for siret, content in files:
                zf.writestr(f"{siret}.{ext}", content)

        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="{siren_export.siren}_registre.zip"'
        return response

    def _fetch_signed_url(self, registry_export_id: str) -> str | None:
        """Return signed download URL from Trackdéchets API, or None on error."""
        client = httpx.Client(timeout=60)
        res = client.post(
            url=settings.TD_API_URL,
            headers={"Authorization": f"Bearer {settings.TD_API_TOKEN}"},
            json={
                "query": graphql_registry_V2_export_download_signed_url,
                "variables": {"exportId": registry_export_id},
            },
        )
        try:
            return res.json()["data"]["registryV2ExportDownloadSignedUrl"]["signedUrl"]
        except (TypeError, KeyError):
            return None

    def _handle_siret_download(self, export):
        """Handle download for single SIRET export"""
        url = self._fetch_signed_url(export.registry_export_id)
        if url is None:
            messages.add_message(self.request, messages.ERROR, "Erreur, le registre n'a pu être téléchargé")
            return HttpResponseRedirect(reverse_lazy("registry_v2_prepare"))
        return HttpResponseRedirect(url)
