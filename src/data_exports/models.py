import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ExportTypeChoice(models.TextChoices):
    BSDD = "BSDD", _("Déchets dangereux")
    BSDA = "BSDA", _("Amiante")
    BSDASRI = "BSDASRI", _("DASRI")
    BSVHU = "BSVHU", _("VHU")
    BSFF = "BSFF", _("Fluides Frigo")


class DataExport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    export_type = models.CharField(
        _("Export Type"),
        max_length=20,
        choices=ExportTypeChoice.choices,
    )
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    name = models.CharField(_("Export name"), max_length=255, blank=True)
    s3_path = models.CharField(_("S3 path"), max_length=512, blank=True)
    last_modified = models.DateTimeField(_("LAst modified"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created at"), default=timezone.now)
    size = models.PositiveIntegerField(_("Size"), null=True, blank=True)
    verbose_size = models.CharField(_("Verbose size"), max_length=64, blank=True)

    class Meta:
        verbose_name = _("Data Export")
        verbose_name_plural = _("Data Exports")
        ordering = ("-created_at",)

    def __str__(self):
        return f"Export {self.export_type} {self.year or 'full'}"


class DataExportDownload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    export_type = models.CharField(
        _("Export Type"),
        max_length=20,
        null=True

    )
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    user = models.CharField(
        _("User email"),
        max_length=256,
    )
    created_at = models.DateTimeField(_("Created at"), default=timezone.now)

    class Meta:
        verbose_name = _("Data Export Download")
        verbose_name_plural = _("Data Exports Downloads")
        ordering = ("-created_at",)

    def __str__(self):
        return f"Export Download {self.export_type} {self.year or 'full'} by {self.user}"
