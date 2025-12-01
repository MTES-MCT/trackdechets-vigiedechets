from django import forms

from faq.models import ASSISTANCE_PAGE_TITLE_LENGTH


class FaqSearchForm(forms.Form):
    q = forms.CharField()


class ContactForm(forms.Form):
    assistance_page_title = forms.CharField(
        widget=forms.HiddenInput(), required=False, max_length=ASSISTANCE_PAGE_TITLE_LENGTH
    )
    subject = forms.CharField(label="Objet", min_length=3, max_length=100)

    body = forms.CharField(label="Question", widget=forms.Textarea(), min_length=20, max_length=3000)
