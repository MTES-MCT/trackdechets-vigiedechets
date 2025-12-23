import datetime as dt

from django.conf import settings
from django.forms import CharField, DateField, Form, ValidationError
from django.forms.widgets import DateInput
from sqlalchemy.sql import text

from .data_extraction import get_wh_sqlachemy_engine
from .queries import sql_company_query_exists_str


class TypedDateInput(DateInput):
    """Django base widget uses text as type for dates"""

    input_type = "date"


class SiretForm(Form):
    siret = CharField(
        max_length=14,
        help_text="Format: 14 chiffres 123 456 789 00099",
    )
    start_date = DateField(
        label="Date de début",
        widget=TypedDateInput,
    )
    end_date = DateField(
        label="Date de fin",
        widget=TypedDateInput,
    )

    def __init__(self, *ars, **kwargs):
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
                raise ValidationError(
                    "Les dates postérieures à aujourd'hui ne sont pas acceptées pour la fiche établissement"
                )
        return end_date

    def clean_siret(self):
        siret = self.cleaned_data["siret"]
        if getattr(settings, "SKIP_SIRET_CHECK", False):
            return siret
        prepared_query = text(sql_company_query_exists_str)

        wh_engine = get_wh_sqlachemy_engine()
        with wh_engine.connect() as con:
            companies = con.execute(prepared_query, {"siret": siret}).all()
        if not companies:
            raise ValidationError("Établissement non inscrit à Trackdéchets.")
        return siret


class SheetPrepareForm(SiretForm):
    is_registry = False
