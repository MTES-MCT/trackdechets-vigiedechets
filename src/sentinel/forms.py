from django import forms

from common.departments import DEPARTMENTS
from sentinel.naf_codes import NAF_CODE_CHOICES

choices = [("", "______________")] + DEPARTMENTS


class NafSearchForm(forms.Form):
    selected_naf_code = forms.ChoiceField(choices=NAF_CODE_CHOICES)
    department = forms.ChoiceField(choices=choices, label="Département")
    page = forms.IntegerField(required=False)
