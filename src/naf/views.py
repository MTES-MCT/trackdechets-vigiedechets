from django import forms
from django.urls import reverse_lazy
from django.views.generic import FormView

from .models import NafCode


class SearchForm(forms.Form):
    text = forms.CharField()


class SearchView(FormView):
    form_class = SearchForm
    template_name = "search.html"
    success_url = reverse_lazy("search")
    results = []

    def form_valid(self, form):
        self.results = NafCode.search(form.cleaned_data["text"])

        return self.render_to_response(self.get_context_data(results=self.results))

    # def get_context_data(self, **kwargs):
    #     return super().get_context_data(**kwargs, results=self.results)
