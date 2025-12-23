from django.utils import timezone
from rest_framework import serializers
from sqlalchemy.sql import text

from sheets.data_extraction import get_wh_sqlachemy_engine
from sheets.models import ComputedInspectionData
from sheets.queries import sql_company_query_exists_str


class ComputedInspectionDataSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()

    class Meta:
        model = ComputedInspectionData
        fields = ["id", "state", "org_id"]

    def get_state(self, obj):
        return obj.api_state


class ComputedInspectionDataCreateSerializer(serializers.Serializer):
    orgId = serializers.CharField()
    year = serializers.IntegerField()

    class Meta:
        fields = [
            "orgId",
            "year",
        ]

    def validate_year(self, year):
        current_year = timezone.now().year
        if year not in [current_year, current_year - 1]:
            raise serializers.ValidationError("Seules l'année en cours et l'année n-1 sont acceptées")
        return year

    def validate_orgId(self, siret):
        prepared_query = text(sql_company_query_exists_str)

        wh_engine = get_wh_sqlachemy_engine()

        with wh_engine.connect() as con:
            companies = con.execute(prepared_query, {"siret": siret}).all()
        if not companies:
            raise serializers.ValidationError("Établissement non inscrit à Trackdéchets.")
        return siret
