from django.forms import CharField, Form, HiddenInput, ValidationError, DateField, MultipleChoiceField, SelectMultiple, TextInput
from sheets.forms import TypedDateInput
from registry.constants import RegistryV2WasteCode


class BsdSearchForm(Form):
    """
    Formulaire de recherche de BSD unifié.
    Le toggle 'search_by_company' active les champs établissement + champs avancés.
    """
    bsd_id = CharField(
        label="N° de bordereau",
        required=False,
        widget=TextInput(attrs={
            "autocomplete": "off",
            "placeholder": "BSD-",
        }),
    )

    # Champs établissement (visibles si toggle ON)
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

    # Champs avancés (visibles si toggle ON)
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

    # Toggle caché
    search_by_company = CharField(required=False, widget=HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        siret = self.data.get("siret")
        bsd_id = self.data.get("bsd_id")
        search_by_company = self.data.get("search_by_company") == "true"

        advanced_fields = [
            "code_dechet", "code_aiot",
            "start_date_rep", "end_date_rep",
            "start_date_exp", "end_date_exp",
        ]

        has_any = bsd_id or (search_by_company and (siret or any(self.data.get(f) for f in advanced_fields)))

        if not has_any:
            raise ValidationError(
                "Au moins un champ de recherche est requis (N° de bordereau ou sélection d'un établissement)."
            )

        start_rep = cleaned_data.get("start_date_rep")
        end_rep = cleaned_data.get("end_date_rep")
        if start_rep and end_rep and start_rep > end_rep:
            self.add_error("end_date_rep", "La date de fin de réception doit être après la date de début.")

        start_exp = cleaned_data.get("start_date_exp")
        end_exp = cleaned_data.get("end_date_exp")
        if start_exp and end_exp and start_exp > end_exp:
            self.add_error("end_date_exp", "La date de fin d'expédition doit être après la date de début.")

        return cleaned_data