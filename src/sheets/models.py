import datetime as dt
import json
import uuid
from datetime import datetime

import numpy as np
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.mail import EmailMessage
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

PENDING = ("PENDING",)
PROCESSED = "PROCESSED"
ERROR = "ERROR"


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        return super().encode(bool(obj)) if isinstance(obj, np.bool_) else super().default(obj)


def notify_admins(pk):
    body = f"La fiche d'inspection {pk} est en erreur"
    message = EmailMessage(
        subject="Une fiche d'inspection est en erreur",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=settings.MESSAGE_RECIPIENTS,
    )
    message.send()


class ComputedInspectionDataCustomManager(models.Manager):
    def mark_as_failed(self, pk):
        self.filter(pk=pk).update(state="COMPUTED_FAILED")
        notify_admins(pk)

    def mark_as_computed(self, pk):
        now = timezone.now()
        self.filter(pk=pk).update(state="COMPUTED", processing_end=now)

    def mark_as_graph_rendered(self, pk):
        now = timezone.now()
        self.filter(pk=pk).update(state="GRAPH_RENDERED", pdf_rendering_end=now)

    def by_web(self):
        return self.filter(creation_mode="WEB")

    def by_api(self):
        return self.filter(creation_mode="API")

    def to_void(self):
        three_month_ago = timezone.now() - dt.timedelta(days=3 * 30)
        return self.filter(created__lte=three_month_ago, voided=False)


class ComputedInspectionData(models.Model):
    class StateChoice(models.TextChoices):
        INITIAL = "INITIAL", _("Initial")
        COMPUTED = "COMPUTED", _("Computed")
        GRAPH_RENDERED = "GRAPH_RENDERED", _("Graph rendered")
        COMPUTED_FAILED = "COMPUTED_FAILED", _("Computation failed")

    class CreationModeChoice(models.TextChoices):
        WEB = "WEB", _("Web")
        API = "API", _("Api")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.CharField(
        _("State"),
        max_length=20,
        choices=StateChoice.choices,
        default=StateChoice.INITIAL,
    )
    org_id = models.CharField(_("Organization ID"), max_length=20)
    data_start_date = models.DateTimeField(_("Data Start Date"), default=datetime(2022, 1, 1))
    data_end_date = models.DateTimeField(_("Data End Date"), default=timezone.now)
    company_name = models.CharField(_("Company Name"), max_length=255, blank=True)
    company_profiles = ArrayField(
        models.CharField(_("Company profiles"), max_length=255),
        blank=True,
        default=list,
    )
    company_collector_profiles = ArrayField(
        models.CharField(_("Company collector profiles"), max_length=255),
        blank=True,
        default=list,
    )
    company_waste_processor_profiles = ArrayField(
        models.CharField(_("Company waste processor profiles"), max_length=255),
        blank=True,
        default=list,
    )
    company_address = models.CharField(_("Company address"), max_length=255, blank=True)
    company_created_at = models.DateTimeField(_("Company created at"), default=timezone.now)
    company_has_enabled_registry_dnd_from_bsd_since = models.DateTimeField(
        _("Company has enabled registry dnd from bsd since"), default=None, null=True
    )
    created = models.DateTimeField(_("Created"), default=timezone.now)

    linked_companies_data = models.JSONField(default=dict)

    bsdd_created_rectified_data = models.JSONField(default=dict)
    bsdd_stock_data = models.JSONField(default=dict)
    bsdd_stats_data = models.JSONField(default=dict, encoder=CustomJSONEncoder)

    bsdd_non_dangerous_created_rectified_data = models.JSONField(default=dict)
    bsdd_non_dangerous_stock_data = models.JSONField(default=dict)
    bsdd_non_dangerous_stats_data = models.JSONField(default=dict, encoder=CustomJSONEncoder)

    bsda_created_rectified_data = models.JSONField(default=dict)
    bsda_stock_data = models.JSONField(default=dict)
    bsda_stats_data = models.JSONField(default=dict, encoder=CustomJSONEncoder)

    bsdasri_created_rectified_data = models.JSONField(default=dict)
    bsdasri_stock_data = models.JSONField(default=dict)
    bsdasri_stats_data = models.JSONField(default=dict, encoder=CustomJSONEncoder)

    bsff_created_rectified_data = models.JSONField(default=dict)
    bsff_stock_data = models.JSONField(default=dict)
    bsff_stats_data = models.JSONField(default=dict, encoder=CustomJSONEncoder)

    bsvhu_created_rectified_data = models.JSONField(default=dict)
    bsvhu_stock_data = models.JSONField(default=dict)
    bsvhu_stats_data = models.JSONField(default=dict, encoder=CustomJSONEncoder)

    all_bsd_data_empty = models.BooleanField(default=True)

    storage_data = models.JSONField(default=dict)

    waste_origin_data = models.JSONField(default=dict)
    waste_origin_map_data = models.JSONField(default=dict)

    waste_flows_data = models.JSONField(default=dict)

    icpe_data = models.JSONField(default=dict)
    agreement_data = models.JSONField(default=dict)
    traceability_interruptions_data = models.JSONField(default=dict)
    waste_is_dangerous_statements_data = models.JSONField(default=dict)
    bsd_canceled_data = models.JSONField(default=dict)
    same_emitter_recipient_data = models.JSONField(default=dict)
    private_individuals_collections_data = models.JSONField(default=dict)
    quantity_outliers_data = models.JSONField(default=dict)

    # Prerendered plotly viz

    bsdd_created_rectified_graph = models.TextField(blank=True)
    bsdd_stock_graph = models.TextField(blank=True)

    bsdd_non_dangerous_created_rectified_graph = models.TextField(blank=True)
    bsdd_non_dangerous_stock_graph = models.TextField(blank=True)

    bsda_created_rectified_graph = models.TextField(blank=True)
    bsda_stock_graph = models.TextField(blank=True)

    bsdasri_created_rectified_graph = models.TextField(blank=True)
    bsdasri_stock_graph = models.TextField(blank=True)

    bsff_created_rectified_graph = models.TextField(blank=True)
    bsff_stock_graph = models.TextField(blank=True)

    bsvhu_created_rectified_graph = models.TextField(blank=True)
    bsvhu_stock_graph = models.TextField(blank=True)

    waste_origin_graph = models.TextField(blank=True)
    waste_origin_map_graph = models.TextField(blank=True)

    icpe_2770_data = models.TextField(blank=True)
    icpe_2770_graph = models.TextField(blank=True)
    icpe_2790_data = models.TextField(blank=True)
    icpe_2790_graph = models.TextField(blank=True)
    icpe_2760_1_data = models.TextField(blank=True)
    icpe_2760_1_graph = models.TextField(blank=True)

    icpe_2771_data = models.TextField(blank=True)
    icpe_2771_graph = models.TextField(blank=True)
    icpe_2791_data = models.TextField(blank=True)
    icpe_2791_graph = models.TextField(blank=True)
    icpe_2760_2_data = models.TextField(blank=True)
    icpe_2760_2_graph = models.TextField(blank=True)

    bs_processed_without_icpe_authorization = models.JSONField(default=dict)

    bsda_worker_stats_data = models.JSONField(default=dict)
    bsda_worker_quantity_data = models.JSONField(default=dict)
    bsda_worker_quantity_graph = models.TextField(blank=True)

    transporter_bordereaux_stats_graph_data = models.JSONField(default=dict)
    transporter_bordereaux_stats_graph = models.TextField(blank=True)
    quantities_transported_stats_graph_data = models.JSONField(default=dict)
    quantities_transported_stats_graph = models.TextField(blank=True)
    transporter_bordereaux_stats_data = models.JSONField(default=dict)

    followed_with_pnttd_data = models.JSONField(default=dict)
    gistrid_stats_data = models.JSONField(default=dict)

    all_registry_data_empty = models.BooleanField(default=True)

    non_dangerous_waste_quantities_graph_data = models.JSONField(default=dict)
    non_dangerous_waste_quantities_graph = models.TextField(blank=True)
    non_dangerous_waste_statements_graph_data = models.JSONField(default=dict)
    non_dangerous_waste_statements_graph = models.TextField(blank=True)
    non_dangerous_waste_stats_data = models.JSONField(default=dict)

    excavated_land_quantities_graph_data = models.JSONField(default=dict)
    excavated_land_quantities_graph = models.TextField(blank=True)
    excavated_land_statements_graph_data = models.JSONField(default=dict)
    excavated_land_statements_graph = models.TextField(blank=True)
    excavated_land_stats_data = models.JSONField(default=dict)

    ssd_quantities_graph_data = models.JSONField(default=dict)
    ssd_quantities_graph = models.TextField(blank=True)
    ssd_statements_graph_data = models.JSONField(default=dict)
    ssd_statements_graph = models.TextField(blank=True)
    ssd_stats_data = models.JSONField(default=dict)
    ssd_table_data = models.JSONField(default=dict)

    registry_transporter_statement_stats_graph_data = models.JSONField(default=dict)
    registry_transporter_statement_stats_graph = models.TextField(blank=True)
    registry_transporter_quantities_graph_data = models.JSONField(default=dict)
    registry_transporter_quantities_graph = models.TextField(blank=True)
    registry_transporter_stats_data = models.JSONField(default=dict)

    eco_organisme_bordereaux_graph_data = models.JSONField(default=dict)
    eco_organisme_bordereaux_graph = models.TextField(blank=True)
    eco_organisme_quantities_graph_data = models.JSONField(default=dict)
    eco_organisme_quantities_graph = models.TextField(blank=True)
    eco_organisme_bordereaux_stats_data = models.JSONField(default=dict)

    eco_organisme_bordereaux_graph_data = models.JSONField(default=dict)
    eco_organisme_bordereaux_graph = models.TextField(blank=True)
    eco_organisme_quantities_graph_data = models.JSONField(default=dict)
    eco_organisme_quantities_graph = models.TextField(blank=True)
    eco_organisme_bordereaux_stats_data = models.JSONField(default=dict)

    incinerator_outgoing_waste_data = models.JSONField(default=dict)

    pdf = models.TextField(blank=True)

    created_by = models.EmailField(verbose_name=_("Created by"), blank=True)
    creation_mode = models.CharField(
        _("Creation Mode"),
        max_length=20,
        choices=CreationModeChoice.choices,
        default=CreationModeChoice.WEB,
    )

    processing_start = models.DateTimeField(_("Processing start"), blank=True, null=True)
    processing_end = models.DateTimeField(_("Processing end"), blank=True, null=True)
    data_extraction_start = models.DateTimeField(_("Data extraction start"), blank=True, null=True)
    data_extraction_end = models.DateTimeField(_("Data extraction end"), blank=True, null=True)
    pdf_rendering_start = models.DateTimeField(_("Pdf rendering start"), blank=True, null=True)
    pdf_rendering_end = models.DateTimeField(_("Pdf rendering end"), blank=True, null=True)
    voided = models.BooleanField(_("Data voided"), default=False, blank=True)  # tell apart voided sheets from other

    objects = ComputedInspectionDataCustomManager()

    class Meta:
        verbose_name = _("Fiche établissement")
        verbose_name_plural = _("Fiches établissement")
        ordering = ("-created",)
        app_label = "sheets"

    def __str__(self):
        return f"Inspection {self.org_id}"

    @property
    def period_start(self):
        return self.data_start_date

    @property
    def period_end(self):
        return self.data_end_date

    @property
    def is_initial(self):
        return self.state == self.StateChoice.INITIAL

    @property
    def is_computed(self):
        return self.state == self.StateChoice.COMPUTED

    @property
    def is_graph_rendered(self):
        return self.state == self.StateChoice.GRAPH_RENDERED

    @property
    def pdf_filename(self):
        return f"FI-Trackdéchets-{self.org_id}-{self.created:%d-%m-%Y}"

    @property
    def api_state(self):
        """Match TD states"""
        return {
            self.StateChoice.INITIAL.name: PENDING,
            self.StateChoice.COMPUTED.name: PENDING,
            self.StateChoice.GRAPH_RENDERED.name: PROCESSED,
            self.StateChoice.COMPUTED_FAILED.name: ERROR,
        }.get(self.state)

    @property
    def processing_duration(self):
        if self.processing_start and self.processing_end:
            return self.processing_end - self.processing_start
        return None

    @property
    def data_extraction_duration(self):
        if self.data_extraction_start and self.data_extraction_end:
            return self.data_extraction_end - self.data_extraction_start
        return None

    @property
    def pdf_rendering_duration(self):
        if self.pdf_rendering_start and self.pdf_rendering_end:
            return self.pdf_rendering_end - self.pdf_rendering_start
        return None

    @classmethod
    def get_json_fields_to_void(cls):
        fields = []
        for field in cls._meta.get_fields():
            if isinstance(field, models.JSONField):
                fields.append(field.name)

        return fields

    @classmethod
    def get_text_fields_to_void(cls):
        fields = []
        for field in cls._meta.get_fields():
            if isinstance(field, models.TextField):
                fields.append(field.name)

        return fields
