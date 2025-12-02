from django.contrib import admin

from .models import DataExport, DataExportDownload


@admin.register(DataExport)
class DataExportAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "export_type",
        "year",
        "name",
        "verbose_size",
        "created_at",
    ]


@admin.register(DataExportDownload)
class DataExportDownloadAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "export_type",
        "year",
        "user",
        "created_at",
    ]
