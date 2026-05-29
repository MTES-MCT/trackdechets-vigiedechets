from django import forms
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from multiupload.fields import MultiFileField

from faq.models import ASSISTANCE_PAGE_TITLE_LENGTH


class FaqSearchForm(forms.Form):
    q = forms.CharField()


class ValidableMultiFileField(MultiFileField):
    def __init__(self, *args, allowed_extensions=None, **kwargs):
        self.allowed_extensions = allowed_extensions or []
        self.data_max_files = kwargs.get("max_num")
        self.data_max_size = kwargs.get("max_file_size")
        self.human_readable_max_size = f"{self.data_max_size / (1024 * 1024):.2f} Mo"
        super().__init__(*args, **kwargs)

    def run_validators(self, value):
        value = value or []
        for item in value:
            super().run_validators(item)

    def clean(self, data, initial=None):
        # 1. On laisse le champ parent faire son nettoyage de base
        files = super().clean(data, initial)

        if not files:
            return files

        # 2. Vérification du nombre maximum de fichiers
        if self.data_max_files and len(files) > self.data_max_files:
            raise ValidationError(f"Vous ne pouvez pas envoyer plus de {self.data_max_files} fichiers.")

        # 3. Vérification de la taille pour chaque fichier
        if self.data_max_size:
            for f in files:
                if f.size > self.data_max_size:
                    raise ValidationError(
                        f"Le fichier {f.name} est trop volumineux. La taille maximale autorisée est de {self.human_readable_max_size}."
                    )

        # Les extensions sont gérées par le FileExtensionValidator déclaré dans le ContactForm
        return files

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs["data-max-files"] = self.data_max_files
        attrs["data-max-size"] = self.data_max_size
        attrs["data-human-readable-max-size"] = self.human_readable_max_size
        if self.allowed_extensions:
            attrs["data-allowed-extensions"] = ",".join(self.allowed_extensions)
        return attrs


class ContactForm(forms.Form):
    assistance_page_title = forms.CharField(
        widget=forms.HiddenInput(), required=False, max_length=ASSISTANCE_PAGE_TITLE_LENGTH
    )
    subject = forms.CharField(label="Objet", min_length=3, max_length=100)

    body = forms.CharField(label="Question", widget=forms.Textarea(), min_length=20, max_length=3000)

    ALLOWED_EXTENSIONS = ["jpg", "png", "pdf", "xls", "doc"]

    files = ValidableMultiFileField(
        label="Fichier(s) – facultatif, jusqu'à 5 fichiers",
        required=False,
        min_num=0,
        max_num=5,
        max_file_size=1024 * 1024 * 2.5,
        allowed_extensions=ALLOWED_EXTENSIONS,
        validators=[FileExtensionValidator(ALLOWED_EXTENSIONS)],
    )
