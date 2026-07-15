import datetime as dt

from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms import ValidationError
from sqlalchemy.sql import text

from sheets.datawarehouse import get_wh_sqlachemy_engine
from sheets.forms import TypedDateInput
from sheets.queries import sql_company_query_exists_str, sql_get_linked_companies_data_from_siren
from sheets.ssh import ssh_tunnel

from .constants import RegistryV2IdentifierType
from .models import RegistryV2Export, RegistryV2ExportSiren, RegistryV2ExportSiret


class RegistryV2PrepareForm(forms.ModelForm):
    """Form for creating registry exports - supports both SIRET and SIREN"""

    identifier_type = forms.ChoiceField(
        label="Type d'identifiant",
        choices=[
            (RegistryV2IdentifierType.SIRET, RegistryV2IdentifierType.SIRET.label),
            (RegistryV2IdentifierType.SIREN, RegistryV2IdentifierType.SIREN.label),
        ],
        widget=forms.RadioSelect,
        initial=RegistryV2IdentifierType.SIRET,
    )

    siret = forms.CharField(
        label="SIRET",
        max_length=14,
        required=False,
        help_text="14 chiffres du SIRET",
    )

    siren = forms.CharField(
        label="SIREN",
        max_length=9,
        required=False,
        help_text="9 chiffres du SIREN",
    )

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

        # Add JavaScript-friendly attributes for conditional display
        self.fields["identifier_type"].widget.attrs.update(
            {
                "data-toggle": "identifier-type",
            }
        )
        self.fields["siret"].widget.attrs.update(
            {
                "data-show-when": RegistryV2IdentifierType.SIRET,
            }
        )
        self.fields["siren"].widget.attrs.update(
            {
                "data-show-when": RegistryV2IdentifierType.SIREN,
            }
        )

    def clean_identifier_type(self):
        identifier_type = self.cleaned_data.get("identifier_type")
        if identifier_type not in [RegistryV2IdentifierType.SIRET, RegistryV2IdentifierType.SIREN]:
            raise ValidationError("Type d'identifiant invalide")
        return identifier_type

    def clean_siret(self):
        siret = self.cleaned_data.get("siret")
        identifier_type = self.cleaned_data.get("identifier_type")

        if identifier_type == RegistryV2IdentifierType.SIRET:
            if not siret:
                raise ValidationError("Le SIRET est requis")
            if not siret.isdigit() or len(siret) != 14:
                raise ValidationError("Le SIRET doit contenir exactement 14 chiffres")

            # Validate SIRET exists in ClickHouse
            if not getattr(settings, "SKIP_SIRET_CHECK", False):
                if not self._siret_exists(siret):
                    raise ValidationError("Établissement non inscrit sur Trackdéchets.")

        return siret

    def clean_siren(self):
        siren = self.cleaned_data.get("siren")
        identifier_type = self.cleaned_data.get("identifier_type")

        if identifier_type == RegistryV2IdentifierType.SIREN:
            if not siren:
                raise ValidationError("Le SIREN est requis")
            if not siren.isdigit() or len(siren) != 9:
                raise ValidationError("Le SIREN doit contenir exactement 9 chiffres")

            # Validate SIREN has at least one SIRET
            if not getattr(settings, "SKIP_SIRET_CHECK", False):
                sirets = self._get_sirets_for_siren(siren)
                if not sirets:
                    raise ValidationError("Aucun établissement trouvé pour ce SIREN sur Trackdéchets.")
                self._cached_sirets = sirets

        return siren

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

        return cleaned_data

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

    def _siret_exists(self, siret):
        """Check if SIRET exists in ClickHouse"""
        prepared_query = text(sql_company_query_exists_str)

        with ssh_tunnel(settings):
            wh_engine = get_wh_sqlachemy_engine()
            with wh_engine.connect() as con:
                companies = con.execute(prepared_query, {"siret": siret}).all()
            return bool(companies)

    def _get_sirets_for_siren(self, siren):
        """Get all SIRETs for a SIREN from ClickHouse"""
        prepared_query = text(sql_get_linked_companies_data_from_siren)

        with ssh_tunnel(settings):
            wh_engine = get_wh_sqlachemy_engine()
            with wh_engine.connect() as con:
                # Use any SIRET starting with this SIREN as parameter
                # (the query uses substring comparison)
                results = con.execute(prepared_query, {"siren": siren}).all()
                return [row[0] for row in results]  # Extract SIRETs

    def save(self, commit=True):
        identifier_type = self.cleaned_data.get("identifier_type")

        if identifier_type == RegistryV2IdentifierType.SIREN:
            # Create SIREN-based export
            siren = self.cleaned_data.get("siren")
            siren_export = RegistryV2ExportSiren(
                siren=siren,
                registry_type=self.cleaned_data.get("registry_type"),
                declaration_type=self.cleaned_data.get("declaration_type"),
                waste_types_dnd=self.cleaned_data.get("waste_types_dnd"),
                waste_types_dd=self.cleaned_data.get("waste_types_dd"),
                waste_types_texs=self.cleaned_data.get("waste_types_texs"),
                waste_codes=self.cleaned_data.get("waste_codes", []),
                start_date=self.cleaned_data.get("start_date"),
                end_date=self.cleaned_data.get("end_date"),
                export_format=self.cleaned_data.get("export_format"),
                created_by=self.created_by,
                created_by_email=self.created_by.email,
            )

            if commit:
                siren_export.save()
                # Create child exports for each SIRET (reuse cached result from clean_siren)
                sirets = getattr(self, "_cached_sirets", None) or self._get_sirets_for_siren(siren)
                siren_export.total_sirets = len(sirets)
                siren_export.save()

                siret_exports = []
                for siret in sirets:
                    siret_exports.append(
                        RegistryV2ExportSiret(
                            parent=siren_export,
                            siret=siret,
                        )
                    )
                RegistryV2ExportSiret.objects.bulk_create(siret_exports)

            return siren_export
        else:
            # Create SIRET-based export (existing logic)
            export = super().save(commit=False)
            export.siret = self.cleaned_data.get("siret")
            export.created_by = self.created_by
            export.created_by_email = self.created_by.email
            export.end_date = export.end_date.replace(hour=23, minute=59, second=59)
            if commit:
                export.save()
            return export

    class Meta:
        model = RegistryV2Export  # Base model for form
        fields = [
            "identifier_type",  # NEW
            "siret",  # Conditional
            "siren",  # NEW, conditional
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
