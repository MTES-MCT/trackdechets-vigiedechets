from django.conf import settings
from django.forms import CharField, Form, HiddenInput, ValidationError, DateField, MultipleChoiceField, SelectMultiple, TextInput
from sqlalchemy.sql import text
from sheets.forms import TypedDateInput

from sheets.data_extraction import get_wh_sqlachemy_engine
from sheets.queries import sql_company_query_exists_str

from registry.constants import RegistryV2WasteCode

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
    """
    Formulaire de recherche de BSD pour la recherche simple (par SIRET, code postal ou numéro de bordereau)
    """
    search_clue = CharField(
        label="Numéro de SIRET ou raison sociale",
        help_text="ou numéro TVA pour un transport dans l'UE",
        required=False,
    )
    siret = CharField(widget=HiddenInput(), required=False)

    code_postal = CharField(
        label="Code postal",
        help_text="Si l'entreprise est française",
        required=False,
    )

    bsd_id = CharField(
    label="N° de bordereau",
    required=False,
    widget=TextInput(attrs={
        "list": "recent-bsds-list",
        "autocomplete": "off",
    }),
    )

    def clean(self):
        cleaned_data = super().clean()
        siret = self.data.get("siret")
        code_postal = self.data.get("code_postal")
        bsd_id = self.data.get("bsd_id")

        if not any([siret, code_postal, bsd_id]):
            raise ValidationError("Au moins un champ de recherche est requis (SIRET, Code postal ou N° de bordereau).")

        return cleaned_data


class BsdAvancedSearchForm(Form):
    """
    Formulaire de recherche de BSD pour la recherche avancée (par SIRET, code postal, numéro de bordereau, code déchet, code aiot et plages de dates)
    """
    search_clue = CharField(
        label="Numéro de SIRET ou raison sociale",
        help_text="ou numéro TVA pour un transport dans l'UE",
        required=False,
    )
    siret = CharField(widget=HiddenInput(), required=False)

    code_postal = CharField(
        label="Code postal",
        help_text="Si l'entreprise est française",
        required=False,
    )

    bsd_id = CharField(
        label="N° de bordereau",
        required=False,
    )

    code_dechet = MultipleChoiceField(
        choices=[(choice.value, choice.value) for choice in RegistryV2WasteCode],
        label="Code déchet",
        required=False,
        widget=SelectMultiple(attrs={"id": "id_code_dechet"}),
    )

    code_aiot = CharField(
        label="Code AIOT",
        required=False,
    )

    start_date_rep = DateField(
        label="Date de début",
        widget=TypedDateInput,
        required=False,
    )

    end_date_rep = DateField(
        label="Date de fin",
        widget=TypedDateInput,
        required=False,
    )

    start_date_exp = DateField(
        label="Date de début",
        widget=TypedDateInput,
        required=False,
    )

    end_date_exp = DateField(
        label="Date de fin",
        widget=TypedDateInput,
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        fields_to_check = [
            "siret", "code_postal", "bsd_id", "code_dechet", "code_aiot",
            "start_date_rep", "end_date_rep", "start_date_exp", "end_date_exp"
        ]
        
        if not any(self.data.get(f) for f in fields_to_check):
            raise ValidationError("Au moins un champ de recherche est requis.")

        start_rep = cleaned_data.get("start_date_rep")
        end_rep = cleaned_data.get("end_date_rep")
        if start_rep and end_rep and start_rep > end_rep:
            self.add_error("end_date_rep", "La date de fin de réception doit être après la date de début.")

        start_exp = cleaned_data.get("start_date_exp")
        end_exp = cleaned_data.get("end_date_exp")
        if start_exp and end_exp and start_exp > end_exp:
            self.add_error("end_date_exp", "La date de fin d'expédition doit être après la date de début.")

        return cleaned_data