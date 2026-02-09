import datetime as dt
import uuid
from datetime import datetime

from django import forms
from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import User

from .constants import (
    RegistryV2DeclarationType,
    RegistryV2ExportState,
    RegistryV2ExportType,
    RegistryV2Format,
    RegistryV2WasteCode,
)
from .managers import RegistryV2ExportQuerySet


class _TypedMultipleChoiceField(forms.TypedMultipleChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.pop("base_field", None)
        kwargs.pop("max_length", None)
        super().__init__(*args, **kwargs)


class ChoiceArrayField(ArrayField):
    """
    A field that allows us to store an array of choices.

    Uses Django 4.2's postgres ArrayField
    and a TypeMultipleChoiceField for its formfield.

    Usage:

        choices = ChoiceArrayField(
            models.CharField(max_length=..., choices=(...,)), blank=[...], default=[...]
        )
    """

    def formfield(self, **kwargs):
        defaults = {
            "form_class": _TypedMultipleChoiceField,
            "choices": self.base_field.choices,
            "coerce": self.base_field.to_python,
        }
        defaults.update(kwargs)
        # Skip our parent's formfield implementation completely as we don't care for it.
        # pylint:disable=bad-super-call
        return super().formfield(**defaults)


class RegistryDownload(models.Model):
    """Deprecated model"""

    org_id = models.CharField(_("Organization ID"), max_length=20)

    data_start_date = models.DateTimeField(_("Data Start Date"), default=datetime(2022, 1, 1))
    data_end_date = models.DateTimeField(_("Data End Date"), default=timezone.now)

    created = models.DateTimeField(_("Created"), default=timezone.now)

    created_by = models.EmailField(verbose_name=_("Created by x"), blank=True)

    class Meta:
        verbose_name = _("Téléchargement de registre")
        verbose_name_plural = _("Téléchargements de registre")
        ordering = ("-created",)


MAX_PROCESSING_DELAY = 10  # minutes


class RegistryV2Export(models.Model):
    """Export V2 model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    siret = models.CharField(_("Établissement concerné"), max_length=20)
    registry_type = models.CharField(
        _("Type de registre"),
        max_length=20,
        choices=RegistryV2ExportType.choices,
        default=RegistryV2ExportType.INCOMING,
    )
    declaration_type = models.CharField(
        _("Type de déclaration"),
        max_length=20,
        choices=RegistryV2DeclarationType.choices,
        default=RegistryV2DeclarationType.ALL,
    )
    waste_types_dnd = models.BooleanField(_("Déchets non dangereux"), default=False, blank=True)
    waste_types_dd = models.BooleanField(_("Déchets dangereux"), default=False, blank=True)
    waste_types_texs = models.BooleanField(_("Terres et sédiments"), default=False, blank=True)

    waste_codes = ChoiceArrayField(
        models.CharField(max_length=32, blank=True, choices=RegistryV2WasteCode),
        verbose_name=_("Codes déchets"),
        default=list,
        blank=True,
    )
    start_date = models.DateTimeField(_("Data Start Date"), default=datetime(2022, 1, 1))
    end_date = models.DateTimeField(_("End Date"), default=timezone.now)
    export_format = models.CharField(
        _("Format d'export"),
        max_length=20,
        choices=RegistryV2Format.choices,
        default=RegistryV2Format.CSV,
    )

    state = models.CharField(
        _("State"),
        max_length=20,
        choices=RegistryV2ExportState.choices,
        default=RegistryV2ExportState.PENDING,
    )

    created_at = models.DateTimeField(_("Created"), default=timezone.now)
    created_by = models.ForeignKey(
        User, verbose_name=_("Created by"), on_delete=models.SET_NULL, blank=True, null=True
    )
    created_by_email = models.EmailField(
        verbose_name=_("Created by email"), blank=True
    )  # keep history if user is deleted

    registry_export_id = models.CharField(_("Trackdéchets Export id"), blank=True)

    objects = RegistryV2ExportQuerySet.as_manager()

    class Meta:
        verbose_name = _("Téléchargement de registre V2")
        verbose_name_plural = _("Téléchargements de registre V2")
        ordering = ("-created_at",)

    def __str__(self):
        return f"Export {self.id} {self.siret}"

    @property
    def successful(self):
        return self.state == RegistryV2ExportState.SUCCESSFUL

    @property
    def is_timeout(self):
        return timezone.now() - self.created_at > dt.timedelta(minutes=MAX_PROCESSING_DELAY)

    @property
    def in_progress(self):
        return self.state in [RegistryV2ExportState.PENDING, RegistryV2ExportState.STARTED] and not self.is_timeout

    @property
    def waste_types(self):
        WASTE_TYPES = ["DND", "DD", "TEXS"]
        bool_vector = [self.waste_types_dnd, self.waste_types_dd, self.waste_types_texs]

        return [item for item, keep in zip(WASTE_TYPES, bool_vector) if keep]

    def mark_as_failed(self):
        self.state = RegistryV2ExportState.FAILED
        self.save()

    def get_gql_variables(self):
        variables = {
            "siret": self.siret,
            "registryType": self.registry_type,
            "format": self.export_format,
            "dateRange": {"_gte": self.start_date.isoformat(), "_lte": self.end_date.isoformat()},
        }
        where = {"declarationType": {"_eq": self.declaration_type}}

        if self.waste_types:
            where.update({"wasteType": {"_in": self.waste_types}})
        if self.waste_codes:
            where.update({"wasteCode": {"_in": self.waste_codes}})

        if where:
            variables.update({"where": where})
        return variables


class RegistryV2ExportSiren(models.Model):
    """Parent export model for SIREN-based exports"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    siren = models.CharField(_("SIREN"), max_length=9, db_index=True)
    registry_type = models.CharField(
        _("Type de registre"),
        max_length=20,
        choices=RegistryV2ExportType.choices,
        default=RegistryV2ExportType.INCOMING,
    )
    declaration_type = models.CharField(
        _("Type de déclaration"),
        max_length=20,
        choices=RegistryV2DeclarationType.choices,
        default=RegistryV2DeclarationType.ALL,
    )
    waste_types_dnd = models.BooleanField(_("Déchets non dangereux"), default=False, blank=True)
    waste_types_dd = models.BooleanField(_("Déchets dangereux"), default=False, blank=True)
    waste_types_texs = models.BooleanField(_("Terres et sédiments"), default=False, blank=True)

    waste_codes = ChoiceArrayField(
        models.CharField(max_length=32, blank=True, choices=RegistryV2WasteCode),
        verbose_name=_("Codes déchets"),
        default=list,
        blank=True,
    )
    start_date = models.DateTimeField(_("Data Start Date"), default=datetime(2022, 1, 1))
    end_date = models.DateTimeField(_("End Date"), default=timezone.now)
    export_format = models.CharField(
        _("Format d'export"),
        max_length=20,
        choices=RegistryV2Format.choices,
        default=RegistryV2Format.CSV,
    )

    state = models.CharField(
        _("State"),
        max_length=20,
        choices=RegistryV2ExportState.choices,
        default=RegistryV2ExportState.PENDING,
    )

    total_sirets = models.IntegerField(_("Total SIRETs"), default=0)
    completed_sirets = models.IntegerField(_("Completed SIRETs"), default=0)
    failed_sirets = models.IntegerField(_("Failed SIRETs"), default=0)

    created_at = models.DateTimeField(_("Created"), default=timezone.now)
    created_by = models.ForeignKey(
        User, verbose_name=_("Created by"), on_delete=models.SET_NULL, blank=True, null=True
    )
    created_by_email = models.EmailField(
        verbose_name=_("Created by email"), blank=True
    )  # keep history if user is deleted

    objects = RegistryV2ExportQuerySet.as_manager()

    class Meta:
        verbose_name = _("Téléchargement de registre V2 (SIREN)")
        verbose_name_plural = _("Téléchargements de registre V2 (SIREN)")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["siren"]),
            models.Index(fields=["state"]),
        ]

    def __str__(self):
        return f"Export SIREN {self.siren} ({self.completed_sirets}/{self.total_sirets})"

    @property
    def successful(self):
        return self.state == RegistryV2ExportState.SUCCESSFUL

    @property
    def is_timeout(self):
        return timezone.now() - self.created_at > dt.timedelta(minutes=MAX_PROCESSING_DELAY)

    @property
    def in_progress(self):
        return self.state in [RegistryV2ExportState.PENDING, RegistryV2ExportState.STARTED] and not self.is_timeout

    @property
    def waste_types(self):
        WASTE_TYPES = ["DND", "DD", "TEXS"]
        bool_vector = [self.waste_types_dnd, self.waste_types_dd, self.waste_types_texs]

        return [item for item, keep in zip(WASTE_TYPES, bool_vector) if keep]

    @property
    def all_sirets_completed(self):
        return self.completed_sirets == self.total_sirets and self.total_sirets > 0

    def update_aggregated_state(self):
        """Recalculate state based on child exports"""
        with transaction.atomic():
            # Lock parent and children to prevent concurrent updates
            # Refresh self with select_for_update to get a locked instance
            locked_self = RegistryV2ExportSiren.objects.select_for_update().get(pk=self.pk)
            children = locked_self.siret_exports.select_for_update().all()
            
            if not children.exists():
                return

            completed = children.filter(state=RegistryV2ExportState.SUCCESSFUL).count()
            failed = children.filter(state=RegistryV2ExportState.FAILED).count()
            in_progress = children.filter(
                state__in=[RegistryV2ExportState.PENDING, RegistryV2ExportState.STARTED]
            ).exists()

            locked_self.completed_sirets = completed
            locked_self.failed_sirets = failed
            locked_self.total_sirets = children.count()

            if completed == locked_self.total_sirets:
                locked_self.state = RegistryV2ExportState.SUCCESSFUL
            elif failed == locked_self.total_sirets:
                locked_self.state = RegistryV2ExportState.FAILED
            elif in_progress:
                locked_self.state = RegistryV2ExportState.STARTED
            elif completed > 0:
                # Partial success - keep as STARTED or add PARTIAL_SUCCESS state
                locked_self.state = RegistryV2ExportState.STARTED

            locked_self.save()
            # Refresh self to reflect changes
            self.refresh_from_db()


class RegistryV2ExportSiret(models.Model):
    """Child export model for individual SIRET within a SIREN export"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(
        RegistryV2ExportSiren,
        related_name="siret_exports",
        on_delete=models.CASCADE,
        db_index=True,
    )
    siret = models.CharField(_("SIRET"), max_length=14, db_index=True)

    state = models.CharField(
        _("State"),
        max_length=20,
        choices=RegistryV2ExportState.choices,
        default=RegistryV2ExportState.PENDING,
    )
    registry_export_id = models.CharField(_("Trackdéchets Export id"), blank=True)

    created_at = models.DateTimeField(_("Created"), default=timezone.now)

    class Meta:
        verbose_name = _("Export SIRET (enfant)")
        verbose_name_plural = _("Exports SIRET (enfants)")
        ordering = ("siret",)
        indexes = [
            models.Index(fields=["parent", "state"]),
            models.Index(fields=["siret"]),
        ]

    def __str__(self):
        return f"{self.siret} (parent: {self.parent.siren})"

    @property
    def successful(self):
        return self.state == RegistryV2ExportState.SUCCESSFUL

    @property
    def is_timeout(self):
        return timezone.now() - self.created_at > dt.timedelta(minutes=MAX_PROCESSING_DELAY)

    @property
    def in_progress(self):
        return self.state in [RegistryV2ExportState.PENDING, RegistryV2ExportState.STARTED] and not self.is_timeout

    def mark_as_failed(self):
        self.state = RegistryV2ExportState.FAILED
        self.save()

    def get_gql_variables(self):
        """Build GraphQL variables using parent's parameters and this SIRET"""
        parent = self.parent
        variables = {
            "siret": self.siret,
            "registryType": parent.registry_type,
            "format": parent.export_format,
            "dateRange": {
                "_gte": parent.start_date.isoformat(),
                "_lte": parent.end_date.isoformat(),
            },
        }
        where = {"declarationType": {"_eq": parent.declaration_type}}

        waste_types = []
        if parent.waste_types_dnd:
            waste_types.append("DND")
        if parent.waste_types_dd:
            waste_types.append("DD")
        if parent.waste_types_texs:
            waste_types.append("TEXS")

        if waste_types:
            where.update({"wasteType": {"_in": waste_types}})
        if parent.waste_codes:
            where.update({"wasteCode": {"_in": parent.waste_codes}})

        if where:
            variables.update({"where": where})
        return variables
