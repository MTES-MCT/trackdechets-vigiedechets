from django.contrib import admin

from .models import BsdPdf, PdfBundle


@admin.register(BsdPdf)
class BsdPdfAdmin(admin.ModelAdmin):
    list_display = ["bsd_id", "company_name", "pdf_file", "created_by", "created_at"]
    list_select_related = [
        "created_by",
    ]
    autocomplete_fields = ["created_by", "bundle"]


class BsdPdfInline(admin.StackedInline):
    model = BsdPdf


@admin.register(PdfBundle)
class PdfBundleAdmin(admin.ModelAdmin):
    list_display = ["id", "company_name", "zip_file", "state", "created_at", "created_by"]
    list_select_related = [
        "created_by",
    ]
    search_fields = [
        "created_by",
    ]
    autocomplete_fields = [
        "created_by",
    ]
    inlines = [
        BsdPdfInline,
    ]
