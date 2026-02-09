from django.contrib import admin

from .models import RegistryDownload, RegistryV2Export, RegistryV2ExportSiren, RegistryV2ExportSiret
from .task import process_export


@admin.register(RegistryDownload)
class RegistryDownloadAdmin(admin.ModelAdmin):
    list_display = ["id", "org_id", "created", "created_by"]
    list_filter = ["created"]
    search_fields = ["org_id"]


@admin.register(RegistryV2Export)
class RegistryV2ExportAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "siret",
        "state",
        "export_format",
        "created_at",
        "registry_type",
        "start_date",
        "end_date",
        "registry_export_id",
        "created_by_email",
    ]
    list_filter = ["registry_type", "export_format", "state"]
    search_fields = ["siret"]
    list_select_related = ["created_by"]
    actions = [
        "action_update_export",
    ]

    @admin.action(description="Refresh registry states by checking Trackdéchets api")
    def action_update_export(self, request, queryset):
        for obj in queryset:
            process_export(obj.pk)


class RegistryV2ExportSiretInline(admin.TabularInline):
    """Inline admin for viewing child SIRET exports"""
    model = RegistryV2ExportSiret
    extra = 0
    readonly_fields = ["id", "siret", "state", "registry_export_id", "created_at"]
    fields = ["siret", "state", "registry_export_id", "created_at"]
    can_delete = False
    show_change_link = True


@admin.register(RegistryV2ExportSiren)
class RegistryV2ExportSirenAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "siren",
        "state",
        "total_sirets",
        "completed_sirets",
        "failed_sirets",
        "export_format",
        "created_at",
        "registry_type",
        "start_date",
        "end_date",
        "created_by_email",
    ]
    list_filter = ["registry_type", "export_format", "state"]
    search_fields = ["siren", "created_by_email"]
    list_select_related = ["created_by"]
    readonly_fields = ["total_sirets", "completed_sirets", "failed_sirets"]
    inlines = [RegistryV2ExportSiretInline]
    actions = [
        "action_update_export",
    ]

    @admin.action(description="Refresh registry states by checking Trackdéchets api")
    def action_update_export(self, request, queryset):
        for obj in queryset:
            process_export(obj.pk)


@admin.register(RegistryV2ExportSiret)
class RegistryV2ExportSiretAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "siret",
        "parent",
        "state",
        "registry_export_id",
        "created_at",
    ]
    list_filter = ["state", "parent"]
    search_fields = ["siret", "parent__siren"]
    list_select_related = ["parent"]
    readonly_fields = ["parent", "siret", "state", "registry_export_id", "created_at"]
