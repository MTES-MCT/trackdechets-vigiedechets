import datetime as dt

from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms import ValidationError
from sqlalchemy.sql import text

from sheets.datawarehouse import get_wh_sqlachemy_engine
from sheets.forms import TypedDateInput
from sheets.queries import sql_company_query_exists_str
from sheets.ssh import ssh_tunnel

from .models import RegistryV2Export


class RegistryV2PrepareForm(forms.ModelForm):
    start_date = forms.DateField(
        label="Date de début",
        widget=TypedDateInput,
    )
    end_date = forms.DateField(
        label="Date de fin",
        widget=TypedDateInput,
    )
    is_registry = True

    def __init__(self, *ars, **kwargs):
        self.created_by = kwargs.pop("created_by", None)
        if self.created_by is None:
            raise ImproperlyConfigured("Missing created_by parameter")

        initial = kwargs.get("initial", {})

        # set initial value and max attrs at form instanciation to prevent unwanted value cache
        today = dt.date.today()
        initial.update(
            {
                "start_date": (today - dt.timedelta(days=365)).isoformat(),
                "end_date": today.isoformat(),
            }
        )
        kwargs["initial"] = initial
        super().__init__(*ars, **kwargs)
        self.fields["start_date"].widget.attrs.update({"max": today.isoformat()})
        self.fields["end_date"].widget.attrs.update(
            {"max": dt.date(day=31, month=12, year=dt.date.today().year).isoformat()}
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if end_date and start_date:
            if end_date <= start_date:
                raise ValidationError("La date de fin doit être postérieure à la date de début")

        waste_types_dnd = cleaned_data.get("waste_types_dnd")
        waste_types_dd = cleaned_data.get("waste_types_dd")
        waste_types_texs = cleaned_data.get("waste_types_texs")
        if not any([waste_types_dnd, waste_types_dd, waste_types_texs]):
            raise ValidationError("Sélectionner au moins un type de déchets")

    def clean_start_date(self):
        start_date = self.cleaned_data["start_date"]
        if start_date > dt.date.today():
            raise ValidationError("Les dates postérieures à aujourd'hui ne sont pas acceptéest")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data["end_date"]

        if self.is_registry:
            current_year = dt.date.today().year
            if end_date.year > current_year:
                raise ValidationError(
                    f"Les dates postérieures à {current_year} ne sont pas acceptées pour le registre"
                )
        else:
            if end_date > dt.date.today():
                raise ValidationError("Les dates postérieures à aujourd'hui ne sont pas acceptées pour le registre")
        return end_date

    def clean_siret(self):
        siret = self.cleaned_data["siret"]
        if getattr(settings, "SKIP_SIRET_CHECK", False):
            return siret
        prepared_query = text(sql_company_query_exists_str)

        with ssh_tunnel(settings):
            wh_engine = get_wh_sqlachemy_engine()
            with wh_engine.connect() as con:
                companies = con.execute(prepared_query, {"siret": siret}).all()
            if not companies:
                raise ValidationError("Établissement non inscrit sur Trackdéchets.")
            return siret

    def save(self, commit=True):
        export = super().save(commit=False)
        export.created_by = self.created_by
        export.created_by_email = self.created_by.email
        if commit:
            export.save()
        return export

    class Meta:
        model = RegistryV2Export
        fields = [
            "siret",
            "registry_type",
            "declaration_type",
            "waste_types_dnd",
            "waste_types_dd",
            "waste_types_texs",
            "waste_codes",
            "start_date",
            "end_date",
            "export_format",
        ]
