from django.contrib import admin
from mptt.admin import MPTTModelAdmin

from .models import NafCode


@admin.register(NafCode)
class NafCodeAdmin(MPTTModelAdmin):
    mptt_level_indent = 30
    list_display = ["code", "content"]
    search_fields = [
        "content",
    ]

    def get_search_results(self, request, queryset, term):
        queryset, _ = super().get_search_results(request, queryset, term)
        if term:
            queryset |= self.model.search(term)

        return queryset, _
