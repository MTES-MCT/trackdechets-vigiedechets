from django import forms

class FaqSearchForm(forms.Form):
    q = forms.CharField()