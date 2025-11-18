from collections import OrderedDict

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminDateWidget
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateRangeFilter

from .models import ComputedInspectionData


class CustomAdminDateWidget(AdminDateWidget):
    input_type = "date"


class CustomDateRangeFilter(DateRangeFilter):
    def _get_form_fields(self):
        return OrderedDict(
            (
                (
                    self.lookup_kwarg_gte,
                    forms.DateField(
                        label="",
                        widget=CustomAdminDateWidget(attrs={"placeholder": _("From date")}),
                        localize=True,
                        required=False,
                        initial=self.default_gte,
                    ),
                ),
                (
                    self.lookup_kwarg_lte,
                    forms.DateField(
                        label="",
                        widget=CustomAdminDateWidget(attrs={"placeholder": _("To date")}),
                        localize=True,
                        required=False,
                        initial=self.default_lte,
                    ),
                ),
            )
        )


def CustomDateRangeFilterBuilder(title=None, default_start=None, default_end=None):
    filter_cls = type(
        str("CustomDateRangeFilter"),
        (CustomDateRangeFilter,),
        {
            "__from_builder": True,
            "default_title": title,
            "default_start": default_start,
            "default_end": default_end,
        },
    )
    return filter_cls


@admin.register(ComputedInspectionData)
class ComputedInspectionDataAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "org_id",
        "company_name",
        "created",
        "get_render",
        "state",
        "data_start_date",
        "data_end_date",
        "creation_mode",
        "created_by",
        "processing_duration",
        "data_extraction_duration",
        "pdf_rendering_duration",
    ]
    list_filter = (("created", CustomDateRangeFilterBuilder()), "creation_mode", "state")
    search_fields = ["id", "org_id"]

    def get_queryset(self, request):
        # Don't load heavy unused fields
        return (
            super()
            .get_queryset(request)
            .only(
                "id",
                "org_id",
                "company_name",
                "created",
                "state",
                "data_start_date",
                "data_end_date",
                "creation_mode",
                "created_by",
                "processing_end",
                "processing_start",
                "data_extraction_end",
                "data_extraction_start",
                "pdf_rendering_end",
                "pdf_rendering_start",
            )
        )

    @admin.display(description="Rendu")
    def get_render(self, obj):
        if obj.state in [
            ComputedInspectionData.StateChoice.INITIAL,
            ComputedInspectionData.StateChoice.COMPUTED_FAILED,
        ]:
            return None
        url = reverse_lazy("sheet", args=[obj.pk])
        return format_html("<a href='{}' _target='blank'>Voir</a>", url)
