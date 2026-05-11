from rest_framework import serializers

from sheets.constants import COLLECTOR_TYPES, COMPANY_TYPES, VHU_PROCESSOR_TYPES, WASTE_PROCESSOR_TYPES

from .centroids import DEPARTMENTS_CENTROIDS, REGIONS_CENTROIDS
from .constants import PROCESSING_OPERATIONS_FIELDS, ROLES_TYPES, WASTE_NAMES
from .models import CartoCompany


class BaseCompanySerializer(serializers.Serializer):
    name = serializers.SerializerMethodField()

    lat = serializers.SerializerMethodField()
    long = serializers.SerializerMethodField()
    count = serializers.IntegerField(source="cnt")
    admin_unit_field = ""
    centroids = {}

    def get_region(self, obj):
        """Cache result"""
        if not obj.get("_cached_admin_unit"):
            code_admin_unit = str(obj[self.admin_unit_field])
            obj["_cached_region"] = self.centroids[code_admin_unit]

        return obj["_cached_region"]

    def get_name(self, obj):
        region = self.get_region(obj)
        return region["name"]

    def get_lat(self, obj):
        region = self.get_region(obj)
        return region["lat"]

    def get_long(self, obj):
        region = self.get_region(obj)
        return region["long"]


class RegionCompanySerializer(BaseCompanySerializer):
    admin_unit_field = "code_region_insee"
    centroids = REGIONS_CENTROIDS


class DepartmentCompanySerializer(BaseCompanySerializer):
    admin_unit_field = "code_departement_insee"
    centroids = DEPARTMENTS_CENTROIDS


class CompanySerializer(serializers.ModelSerializer):
    lat = serializers.SerializerMethodField()
    long = serializers.SerializerMethodField()
    wastes = serializers.SerializerMethodField()
    profiles = serializers.SerializerMethodField()

    class Meta:
        model = CartoCompany
        fields = (
            "siret",
            "nom_etablissement",
            "adresse_td",
            "lat",
            "long",
            "wastes",
            "profiles",
            "registered_on_td",
            "is_dormant",
        )

    def get_lat(self, obj):
        return obj.coords[1]

    def get_long(self, obj):
        return obj.coords[0]

    def get_wastes(self, obj):
        vector = [
            obj.bsdd,
            obj.bsda,
            obj.bsff,
            obj.bsdasri,
            obj.bsvhu,
            obj.ssd,
            obj.bsdnd,
            obj.texs,
            obj.texs_dd,
        ]

        return ", ".join([n for i, n in enumerate(WASTE_NAMES) if vector[i]])

    def get_profiles(self, obj):
        if not obj.profils:
            return ""

        return ", ".join([COMPANY_TYPES.get(p) for p in obj.profils if p in COMPANY_TYPES])


class ClusterSerializer(serializers.Serializer):
    lat = serializers.SerializerMethodField()
    long = serializers.SerializerMethodField()
    count = serializers.IntegerField()

    def get_lat(self, obj):
        return obj["location"].coords[1]

    def get_long(self, obj):
        return obj["location"].coords[0]


VERBOSE_ROLES = {
    "emitter": "Producteur - émetteur",
    "transporter": "Transporteur",
    "worker": "Entreprise de travaux",
    "destination": "Destinataire",
}


class CompanyExportSerializer(serializers.ModelSerializer):
    """
    Specialized serializer for company exports that includes basic information
    and role information formatted as comma-separated values.
    """

    siret = serializers.CharField()
    nom_etablissement = serializers.CharField()
    adresse_td = serializers.CharField()

    # Role fields as string representations
    bsdd_roles = serializers.SerializerMethodField()
    bsdnd_roles = serializers.SerializerMethodField()
    bsda_roles = serializers.SerializerMethodField()
    bsff_roles = serializers.SerializerMethodField()
    bsdasri_roles = serializers.SerializerMethodField()
    bsvhu_roles = serializers.SerializerMethodField()
    texs_dd_roles = serializers.SerializerMethodField()
    dnd_roles = serializers.SerializerMethodField()
    texs_roles = serializers.SerializerMethodField()

    profiles = serializers.SerializerMethodField()
    collector_profiles = serializers.SerializerMethodField()
    installation_profiles = serializers.SerializerMethodField()
    vhu_installation_profiles = serializers.SerializerMethodField()

    processing_operations = serializers.SerializerMethodField()

    class Meta:
        model = CartoCompany
        fields = [
            "siret",
            "nom_etablissement",
            "adresse_td",
            "profiles",
            "collector_profiles",
            "installation_profiles",
            "vhu_installation_profiles",
            "bsdd_roles",
            "bsdnd_roles",
            "bsda_roles",
            "bsff_roles",
            "bsdasri_roles",
            "bsvhu_roles",
            "texs_dd_roles",
            "dnd_roles",
            "texs_roles",
            "processing_operations",
            "is_dormant",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for waste_type in ROLES_TYPES:
            setattr(self, f"get_{waste_type}_roles", self._create_get_roles_method(waste_type))

    def _create_get_roles_method(self, waste_type):
        def get_roles(obj):
            roles = []
            for role in ROLES_TYPES[waste_type]:
                field_name = f"{waste_type}_{role}"
                if getattr(obj, field_name, False):
                    verbose_role = VERBOSE_ROLES.get(role, role)
                    roles.append(verbose_role)
            return ", ".join(roles) if roles else ""

        return get_roles

    def get_processing_operations(self, obj):
        """Combines processing operations into a string field"""
        all_operations = []

        # Combine operations from different fields
        for field_name in PROCESSING_OPERATIONS_FIELDS:
            operations = getattr(obj, field_name, None)
            if operations:
                all_operations.extend(operations)

        return ", ".join(sorted(set(all_operations))) if all_operations else ""

    def get_profiles(self, obj):
        if not obj.profils:
            return ""

        return ", ".join([COMPANY_TYPES.get(p) for p in obj.profils if p in COMPANY_TYPES])

    def get_collector_profiles(self, obj):
        if not obj.profils_collecteur:
            return ""

        return ", ".join([COLLECTOR_TYPES.get(p) for p in obj.profils_collecteur if p in COLLECTOR_TYPES])

    def get_installation_profiles(self, obj):
        if not obj.profils_installation:
            return ""

        return ", ".join(
            [WASTE_PROCESSOR_TYPES.get(p) for p in obj.profils_installation if p in WASTE_PROCESSOR_TYPES]
        )

    def get_vhu_installation_profiles(self, obj):
        if not obj.profils_installation_vhu:
            return ""

        return ", ".join(
            [VHU_PROCESSOR_TYPES.get(p) for p in obj.profils_installation_vhu if p in VHU_PROCESSOR_TYPES]
        )
