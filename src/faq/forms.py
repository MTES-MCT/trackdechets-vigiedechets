from django import forms
from django.core.validators import FileExtensionValidator
from multiupload.fields import MultiFileField

from faq.models import ASSISTANCE_PAGE_TITLE_LENGTH


class FaqSearchForm(forms.Form):
    q = forms.CharField()


class ValidableMultiFileField(MultiFileField):
    def run_validators(self, value):
        value = value or []

        for item in value:
            super().run_validators(item)


class ContactForm(forms.Form):
    assistance_page_title = forms.CharField(
        widget=forms.HiddenInput(), required=False, max_length=ASSISTANCE_PAGE_TITLE_LENGTH
    )
    subject = forms.CharField(label="Objet", min_length=3, max_length=100)

    body = forms.CharField(label="Question", widget=forms.Textarea(), min_length=20, max_length=3000)

    files = ValidableMultiFileField(
        label="Fichier(s)",
        required=False,
        min_num=0,
        max_num=5,
        max_file_size=1024 * 1024 * 2.5,
        validators=[FileExtensionValidator(["pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"])],
    )
