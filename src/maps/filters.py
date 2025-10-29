from functools import reduce
from operator import ior

from django.contrib.gis.geos import Point, Polygon
from django.db.models import Q
from django_filters import rest_framework as filters

from .constants import BASE_ROLES_TYPES, BSD_TYPES, ROLES_CONFIG, ROLES_TYPES
from .models import CartoCompany


def prepare_role_specific_fields():
    """
    Create a list containing all possible combinations of waste types and roles for filtering purposes
    eg. 'bsdd_emitter', 'bsdd_transporter', 'bsdd_destination' etc.
    """
    role_specific_fields = []
    for waste_type, roles in ROLES_TYPES.items():
        for role in roles:
            field_name = f"{waste_type}_{role}"
            role_specific_fields.append(field_name)

    return role_specific_fields


ROLE_SPECIFIC_FIELDS = prepare_role_specific_fields()


# not all bsd types have a matching processing_operations_* field
BSD_TYPES_FOR_OPERATION_CODE = [bsd_type for bsd_type, config in ROLES_CONFIG.items() if config["code_operation"]]


def remove_after_last_underscore(s):
    """Handle strings like bsdasri_emitter and text_dd_transporter"""
    parts = s.rsplit("_", 1)
    return parts[0]


def map_to_operation_field(val):
    if val == "texs_dd":  # because our data scientist is too lazy to handle separately `texs` and `texs_dd`
        return "texs"
    return val


class CartoCompanyFilter(filters.FilterSet):
    departments = filters.CharFilter(method="filter_departments")
    profils = filters.CharFilter(method="filter_profils")
    profils_collecteur = filters.CharFilter(method="filter_profils_collecteur")
    profils_installation = filters.CharFilter(method="filter_profils_installation")
    profils_installation_vhu = filters.CharFilter(method="filter_profils_installation_vhu")
    bsds_roles = filters.CharFilter(method="filter_bsds_roles")
    operation_codes = filters.CharFilter(method="filter_operation_codes")
    waste_codes = filters.CharFilter(method="filter_waste_codes")
    bounds = filters.CharFilter(method="filter_bounds", required=True)

    def filter_departments(self, queryset, _, value):
        return queryset.filter(code_departement_insee__in=value.split(","))

    def filter_profils(self, queryset, _, value):
        return queryset.filter(profils__contains=value.split(","))

    def filter_profils_collecteur(self, queryset, _, value):
        return queryset.filter(profils_collecteur__contains=value.split(","))

    def filter_profils_installation(self, queryset, name, value):
        return queryset.filter(profils_installation__contains=value.split(","))

    def filter_profils_installation_vhu(self, queryset, name, value):
        return queryset.filter(profils_installation_vhu__contains=value.split(","))

    def filter_waste_codes(self, queryset, name, value):
        return queryset.filter(waste_codes_bordereaux__overlap=value.split(","))

    def filter_operation_codes(self, queryset, name, value):
        # get a list of operation codes eg. ["R1", "R6"]
        values = value.split(",")

        if not values:
            return queryset
        # extract bsd types
        bsds_roles_values = self.data.get("bsds_roles", "").split(",")
        bsd_types = list(set([remove_after_last_underscore(role) for role in bsds_roles_values]))

        # ensure bsd_types exist and are allowed here
        bsd_types = [map_to_operation_field(v) for v in bsd_types if v in BSD_TYPES_FOR_OPERATION_CODE]
        # Bsd types not selected:  consider all bsds types

        if not bsd_types:
            bsd_types = BSD_TYPES_FOR_OPERATION_CODE
        # now query each relevant field eg. processing_operations_bsdasri__overlap: ["R1", "R6"]
        queryterms = [Q(**{f"processing_operations_{field}__overlap": values}) for field in bsd_types]
        if not queryterms:
            return queryset
        params = reduce(ior, queryterms)

        return queryset.filter(params)

    def filter_bounds(self, queryset, name, value):
        bbox = [float(v) for v in value.split(",")]

        p1 = Point(bbox[0], bbox[1], srid=4326)
        p2 = Point(bbox[2], bbox[3], srid=4326)
        diagonal = p1.distance(p2)
        if diagonal >= 2:  # explain
            return queryset

        bbox_polygon = Polygon.from_bbox(bbox)

        return queryset.filter(coords__within=bbox_polygon)

    def filter_bsds_roles(self, queryset, name, value):
        # Role types to check for each base type

        requested_roles = value.split(",")
        queryterms = []

        for requested_role in requested_roles:
            # handle bsdd + role when both are provided
            if requested_role in ROLE_SPECIFIC_FIELDS:
                queryterms.append(Q(**{requested_role: True}))
            # handle role only field to query all specific fields: bsda_emitter + bsdasri_emitter etc…
            if requested_role in BASE_ROLES_TYPES:
                queryterms += [Q(**{f"{bsd_type}_{requested_role}": True}) for bsd_type in BSD_TYPES]
            # handle bsd type only field: bsda, bsvhu etc…
            if requested_role in BSD_TYPES_FOR_OPERATION_CODE:
                queryterms.append(Q(**{requested_role: True}))

        if not queryterms:
            return queryset

        params = reduce(ior, queryterms)

        return queryset.filter(params)

    class Meta:
        model = CartoCompany
        fields = [
            "bsdd",
            "bsdnd",
            "bsda",
            "bsff",
            "bsdasri",
            "bsvhu",
            "texs_dd",
            "dnd",
            "texs",
            # "bsds",
            "bsds_roles",
            "profils",
            # BSDD roles
            "bsdd_emitter",
            "bsdd_transporter",
            "bsdd_destination",
            # BSDND roles
            "bsdnd_emitter",
            "bsdnd_transporter",
            "bsdnd_destination",
            # BSDA roles
            "bsda_emitter",
            "bsda_transporter",
            "bsda_destination",
            # BSFF roles
            "bsff_emitter",
            "bsff_transporter",
            "bsff_destination",
            # BSDASRI roles
            "bsdasri_emitter",
            "bsdasri_transporter",
            "bsdasri_destination",
            # BSVHU roles
            "bsvhu_emitter",
            "bsvhu_transporter",
            "bsvhu_destination",
            # TEXS_DD roles
            "texs_dd_emitter",
            "texs_dd_transporter",
            "texs_dd_destination",
            # DND roles
            "dnd_emitter",
            "dnd_destination",
            # TEXS roles
            "texs_emitter",
            "texs_destination",
            # ssd
            "ssd",
        ]
