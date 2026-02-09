import csv
import io
import json
import math

import pandas as pd
from django.contrib.gis.geos import Point
from django.db.models import Count
from django.http import FileResponse, Http404, HttpResponse
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .centroids import DEPARTMENTS_CENTROIDS, REGIONS_CENTROIDS
from .constants import ANNUAL_ICPE_RUBRIQUES
from .filters import CartoCompanyFilter
from .models import (
    CartoCompany,
    DepartementsComputation,
    FranceComputation,
    InstallationsComputation,
    RegionsComputation,
)
from .permissions import UserIsVerifedPermission
from .serializers import (
    CompanyExportSerializer,
    CompanySerializer,
    DepartmentCompanySerializer,
    RegionCompanySerializer,
)

empty_response_data = {"companies": [], "clusters": [], "total_count": 0}

available_departments_code = DEPARTMENTS_CENTROIDS.keys()
available_regions_code = REGIONS_CENTROIDS.keys()

MAX_EXPORT_ROWS = 1500


class ApiObjects(ListAPIView):
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = CartoCompanyFilter
    authentication_classes = [SessionAuthentication]
    permission_classes = [UserIsVerifedPermission]
    serializer_class = None

    def get_total_count(self, queryset):
        """
        Count total companies matching filter criteria without bounds filter
        """
        # Create a copy of request.GET without the bounds parameter
        filter_params = self.request.GET.copy()
        if "bounds" in filter_params:
            filter_params.pop("bounds")

        # Apply all filters except bounds
        filterset = self.filterset_class(filter_params, CartoCompany.objects.exclude(coords__isnull=True))

        return filterset.qs.count()

    def get_queryset(self):
        DIAGONAL_REGIONS = 10
        DIAGONAL_DEPARTMENTS = 2
        if self.diagonal >= DIAGONAL_REGIONS:
            return self.get_regions()
        if self.diagonal >= DIAGONAL_DEPARTMENTS:
            return self.get_departments()
        return CartoCompany.objects.exclude(coords__isnull=True)

    def get_regions(self):
        return (
            CartoCompany.objects.filter(code_region_insee__in=available_regions_code)
            .values("code_region_insee")
            .annotate(cnt=Count("code_region_insee"))
            .order_by()
        )

    def get_departments(self):
        return (
            CartoCompany.objects.filter(code_departement_insee__in=available_departments_code)
            .values("code_departement_insee")
            .annotate(cnt=Count("code_departement_insee"))
            .order_by()
        )

    def get_serializer(self, *args, **kwargs):
        if self.diagonal >= 10:
            return RegionCompanySerializer
        if self.diagonal >= 2:
            return DepartmentCompanySerializer
        return CompanySerializer

    def list(self, request, *args, **kwargs):
        bounds = self.request.GET.get("bounds")
        if not bounds:
            return Response(empty_response_data)

        bbox = [float(v) for v in bounds.split(",")]
        p1 = Point(bbox[0], bbox[1], srid=4326)
        p2 = Point(bbox[2], bbox[3], srid=4326)
        self.diagonal = p1.distance(p2)
        queryset = self.get_queryset()
        filtered_queryset = self.filter_queryset(queryset)

        total_count = self.get_total_count(queryset)

        serializer = self.get_serializer()

        if self.diagonal >= 2:
            clusters = serializer(filtered_queryset, many=True).data
            response_data = {
                "companies": [],
                "clusters": clusters,  # Empty clusters when showing individual companies
                "total_count": total_count,
            }
            return Response(response_data)

        companies = serializer(filtered_queryset, many=True).data
        response_data = {
            "companies": companies,
            "clusters": [],  # Empty clusters when showing individual companies
            "total_count": total_count,
        }
        return Response(response_data)


class ApiCompanyExport(APIView):
    """
    API endpoint to export filtered companies data as CSV or Excel

    Query parameters:
    - format: 'csv' or 'xlsx' (default: 'csv')
    - any company filter parameters (see CartoCompanyFilter class)

    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [UserIsVerifedPermission]

    def post(self, request, *args, **kwargs):
        return self._process_export_request(request)

    def _process_export_request(self, request):
        # Apply the same filtering as in the existing API
        queryset = CartoCompany.objects.exclude(coords__isnull=True)
        filterset = CartoCompanyFilter(request.query_params, queryset)

        filtered_companies = filterset.qs
        if len(filtered_companies) > MAX_EXPORT_ROWS:
            return Response(
                {
                    "error": "Too many results",
                    "detail": f"Export limité à {MAX_EXPORT_ROWS} établissments.",
                },
                status=400,
            )

        serializer = CompanyExportSerializer(filtered_companies, many=True)
        data = serializer.data
        # Determine the export format (default to XLSX)
        export_format = request.query_params.get("export_format", "xlsx")

        if export_format == "xlsx":
            return self._export_excel(data)
        else:  # default to CSV
            return self._export_csv(data)

    def get_filename(self):
        dt = timezone.now()
        return f"export-{dt.strftime('%Y-%m-%d_%H%M%S')}"

    def _export_csv(self, data):
        response = HttpResponse(content_type="text/csv")
        filename = self.get_filename()
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'

        if not data:
            # Handle empty data case
            response.write("")
            return response

        fieldnames = data[0].keys()

        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()

        for row in data:
            writer.writerow(row)

        return response

    def _export_excel(self, data):
        filename = self.get_filename()
        output = io.BytesIO()

        df = pd.DataFrame(data if data else [])
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Companies", index=False)

        # Set up the response
        output.seek(0)
        response = FileResponse(
            output, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'

        return response


class ICPEViewMany(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [UserIsVerifedPermission]

    def get(self, request, layer, year, rubrique):
        layers_configs = {
            "installations": {
                "cls": InstallationsComputation,
                "fields": [
                    "code_aiot",
                    "latitude",
                    "longitude",
                    "raison_sociale",
                    "siret",
                    "adresse1",
                    "adresse2",
                    "code_postal",
                    "commune",
                    "etat_activite",
                    "regime",
                    "unite",
                    "quantite_autorisee",
                    "taux_consommation",
                    "moyenne_quantite_journaliere_traitee",
                    "cumul_quantite_traitee",
                ],
                "layer_key": "code_aiot",
            },
            "departements": {
                "cls": DepartementsComputation,
                "fields": [
                    "code_departement_insee",
                    "nom_departement",
                    "quantite_autorisee",
                    "taux_consommation",
                    "moyenne_quantite_journaliere_traitee",
                    "cumul_quantite_traitee",
                    "nombre_installations",
                ],
                "layer_key": "code_departement_insee",
            },
            "regions": {
                "cls": RegionsComputation,
                "fields": [
                    "code_region_insee",
                    "nom_region",
                    "quantite_autorisee",
                    "taux_consommation",
                    "moyenne_quantite_journaliere_traitee",
                    "cumul_quantite_traitee",
                    "nombre_installations",
                ],
                "layer_key": "code_region_insee",
            },
            "france": {
                "cls": FranceComputation,
                "fields": [
                    "code_region_insee",
                    "nom_region",
                    "quantite_autorisee",
                    "taux_consommation",
                    "moyenne_quantite_journaliere_traitee",
                    "cumul_quantite_traitee",
                    "nombre_installations",
                ],
                "layer_key": None,
            },
        }

        layer_config = layers_configs[layer]
        model = layer_config["cls"]
        fields = layer_config["fields"]
        layer_key = layer_config["layer_key"]

        results = {}

        for obj in model.objects.filter(year=year, rubrique=rubrique).values(*fields):
            obj_clean = {
                k: e if not isinstance(e, float) or not (math.isnan(e) or math.isinf(e)) else None
                for k, e in obj.items()
            }
            results[obj_clean[layer_key]] = obj_clean

        if not results:
            raise Http404
        return Response({"data": results})


class ICPEGraph(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [UserIsVerifedPermission]

    def get(self, request, layer, year, rubrique, code):
        layers_configs = {
            "installations": {
                "cls": InstallationsComputation,
                "specific_filter": {"code_aiot": code},
            },
            "departements": {
                "cls": DepartementsComputation,
                "specific_filter": {"code_departement_insee": code},
            },
            "regions": {
                "cls": RegionsComputation,
                "specific_filter": {"code_region_insee": code},
            },
        }

        layer_config = layers_configs[layer]
        model = layer_config["cls"]
        specific_filter = layer_config["specific_filter"]
        result = model.objects.filter(year=year, rubrique=rubrique, **specific_filter).values("graph").first()
        if not result:
            raise Http404

        resp = {"graph": None}
        if result["graph"] is not None:
            resp = {"graph": json.loads(result["graph"])}

        return Response(resp)


class ICPEFrance(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [UserIsVerifedPermission]

    def get(self, request, year, rubrique):
        fields = [
            "quantite_autorisee",
            "moyenne_quantite_journaliere_traitee",
            "cumul_quantite_traitee",
            "taux_consommation",
            "nombre_installations",
            "graph",
        ]
        result = FranceComputation.objects.filter(year=year, rubrique=rubrique).first()

        if not result:
            raise Http404

        result_dict = {}
        for k in fields:
            val = getattr(result, k)

            if k == "graph":
                result_dict[k] = json.loads(val)
            elif isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                result_dict[k] = None
            else:
                result_dict[k] = val

        return Response({"data": result_dict})
