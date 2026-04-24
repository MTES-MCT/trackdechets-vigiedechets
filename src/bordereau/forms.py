from django.conf import settings
from django.forms import CharField, Form, HiddenInput, ValidationError, DateField, MultipleChoiceField, SelectMultiple, TextInput
from sqlalchemy.sql import text
from sheets.forms import TypedDateInput

from sheets.data_extraction import get_wh_sqlachemy_engine

from registry.constants import RegistryV2WasteCode

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
        "placeholder": "BSD-",
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
    widget=TextInput(attrs={
        "list": "recent-bsds-list",
        "autocomplete": "off",
        "placeholder": "BSD-",
    }),
    )

    code_dechet = MultipleChoiceField(
        choices=[(choice.value, choice.value) for choice in RegistryV2WasteCode],
        label="Code déchet",
        required=False,
        widget=SelectMultiple(attrs={"id": "id_code_dechet"}),
    )

    code_aiot = CharField(
        label="Code MonAIOT",
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