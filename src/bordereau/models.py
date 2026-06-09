import uuid

from django.core.files.storage import storages
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import User


class PdfBundleQuerySet(models.QuerySet):
    def ready(self):
        return self.filter(state="READY")


class PdfBundleManager(models.Manager.from_queryset(PdfBundleQuerySet)):
    def mark_as_failed(self, pk):
        self.filter(pk=pk).update(state="ERROR")

    def mark_as_processing(self, pk):
        self.filter(pk=pk).update(state="PROCESSING")

    def mark_as_ready(self, pk):
        self.filter(pk=pk).update(state="READY")


def bundle_path(instance, _):
    now = timezone.now()
    siret = instance.search_params.get("siret", "Tous") if instance.search_params else "Tous"
    return f"bordereaux_bundles/{now.year}/{now.month}/{now.day}/{now.year}{now.month}{now.day}_{now.hour}{now.minute}_{siret}.zip"


class PdfBundle(models.Model):
    class BundleChoice(models.TextChoices):
        INITIAL = "INITIAL", _("Initial")
        PROCESSING = "PROCESSING", _("Processing")
        READY = "READY", _("Ready")
        ERROR = "ERROR", _("Error")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    params = models.JSONField(default=dict)
    search_params = models.JSONField(default=dict, blank=True)

    state = models.CharField(
        _("State"),
        max_length=20,
        choices=BundleChoice.choices,
        default=BundleChoice.INITIAL,
    )
    created_at = models.DateTimeField(_("Downloaded at"), default=timezone.now)
    created_by = models.ForeignKey(
        User,
        verbose_name=_("Created by"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="bordereau_pdfbundles",
    )
    zip_file = models.FileField(
        _("Zip File"), upload_to=bundle_path, blank=True, max_length=512, storage=storages["private_s3"]
    )
    objects = PdfBundleManager()

    class Meta:
        verbose_name = _("Pdfs Bundle")
        verbose_name_plural = _("Pdfs Bundles")
        ordering = ("-created_at",)

    @property
    def type(self):
        return "Bundle"

    @property
    def verbose_type(self):
        return "Dossier"

    def __str__(self):
        siret = self.search_params.get("siret", "Tous") if self.search_params else "Tous"
        return f"Archive {siret} {self.created_at.strftime('%d %M %Y')}"


def bsd_path(instance, _):
    now = timezone.now()
    return f"bordereaux_bsds/{now.year}/{now.month}/{now.day}/bsd-{instance.id}.pdf"


class BsdPdf(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bsd_id = models.CharField(_("Bsd Id "), max_length=30)
    packagings = models.CharField(_("Packagings"), max_length=255, blank=True)
    waste_code = models.CharField(_("Waste Code"), max_length=128, blank=True)
    weight = models.CharField(_("Weight"), max_length=30, blank=True, null=True)
    adr_code = models.CharField(_("Adr Code"), max_length=255, blank=True)
    created_at = models.DateTimeField(_("Created at"), default=timezone.now)
    pdf_file = models.FileField(
        _("Pdf"), upload_to=bsd_path, blank=True, max_length=512, storage=storages["private_s3"]
    )
    created_by = models.ForeignKey(
        User,
        verbose_name=_("Created by"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="bordereau_bsdpdfs",
    )
    bundle = models.ForeignKey(
        PdfBundle, verbose_name=_("Bundle"), blank=True, null=True, on_delete=models.CASCADE, related_name="pdfs"
    )

    class Meta:
        verbose_name = _("Pdf Bsd")
        verbose_name_plural = _("Pdfs Bsds")
        ordering = ("-created_at",)

    def __str__(self):
        return f"Pdf {self.bsd_id}"

    @property
    def bsd_file_name(self):
        return f"{self.bsd_id}.pdf"

    @property
    def type(self):
        return "Pdf"

    @property
    def verbose_type(self):
        return "Bordereau"


@receiver(pre_delete, sender=PdfBundle)
def delete_pdf_bundle_files(sender, instance, *args, **kwargs):
    """Supprime le fichier ZIP sur S3 lors de la suppression du bundle"""
    if instance.zip_file:
        instance.zip_file.delete(save=False)


@receiver(pre_delete, sender=BsdPdf)
def delete_bsd_pdf_files(sender, instance, *args, **kwargs):
    """Supprime le fichier PDF sur S3 lors de la suppression d'un bordereau individuel"""
    if instance.pdf_file:
        instance.pdf_file.delete(save=False)
