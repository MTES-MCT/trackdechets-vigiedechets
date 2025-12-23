from django.conf import settings
from django.forms import CharField, Form, HiddenInput, ValidationError
from sqlalchemy.sql import text

from sheets.data_extraction import get_wh_sqlachemy_engine
from sheets.queries import sql_company_query_exists_str


class RoadControlSearchForm(Form):
    siret = CharField(
        label="Numéro de SIRET",
        min_length=14,
        max_length=17,
        help_text="Format: 14 chiffres 123 456 789 00099",
        required=False,
    )

    plate = CharField(
        label="Immatriculation",
        min_length=2,
        max_length=14,
        help_text="Format: 5-14 caractères (AB-123-YZ ou AB 123 YZ)",
        required=False,
    )
    end_cursor = CharField(required=False, widget=HiddenInput())

    def clean_plate(self):
        plate = self.cleaned_data["plate"]
        plate = plate.replace("-", " ")
        plate = " ".join(plate.split())  # strip double whitespace
        return plate

    def clean_siret(self):
        siret = self.cleaned_data["siret"]

        if not siret:
            return siret
        siret = "".join(siret.split())  # strip all whitespace

        prepared_query = text(sql_company_query_exists_str)

        if not settings.SKIP_ROAD_CONTROL_SIRET_CHECK:
            wh_engine = get_wh_sqlachemy_engine()
            with wh_engine.connect() as con:
                companies = con.execute(prepared_query, {"siret": siret}).all()

            if not companies:
                raise ValidationError("Établissement non inscrit sur Trackdéchets.")
        return siret

    def clean(self):
        cleaned_data = super().clean()
        plate = cleaned_data.get("plate")
        siret = cleaned_data.get("siret")
        if not plate and not siret:
            raise ValidationError("Au moins un champ est requis")

        if len("".join(plate.split())) < 6 and not siret:
            self.add_error(
                "plate", "L'immatriculation doit être renseignée en entier si vous ne précisez pas le siret"
            )


class BsdSearchForm(Form):
    bsd_id = CharField(
        label="Numéro de bordereau",
        min_length=18,
        max_length=22,
        required=True,
    )
