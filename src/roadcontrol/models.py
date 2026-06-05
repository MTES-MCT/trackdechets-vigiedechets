import uuid

from django.core.files.storage import storages
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import User


class PdfBundleQuerySet(models.QuerySet):
    def road_control(self):
        return self.filter(request_type="ROAD_CONTROL")

    def bsd(self):
        return self.filter(request_type="BSD")

    def ready(self):
        return self.filter(state="READY")


class PdfBundleManager(models.Manager.from_queryset(PdfBundleQuerySet)):
    def mark_as_failed(self, pk):
        self.filter(pk=pk).update(state="ERROR")

    def mark_as_processing(self, pk):
        self.filter(pk=pk).update(state="PROCESSING")

    def mark_as_ready(self, pk):
        self.filter(pk=pk).update(state="READY")

class Base(models.Model):
    company_siret = models.CharField(_("Company Siret"), max_length=20, blank=True)
    company_name = models.CharField(_("Company Name"), max_length=255, blank=True)
    company_address = models.CharField(_("Company Address"), max_length=512, blank=True)
    company_contact = models.CharField(_("Company Contact"), max_length=255, blank=True)
    company_email = models.EmailField(_("Company Email"), max_length=255, blank=True)
    company_phone = models.CharField(_("Company Phone"), max_length=20, blank=True)
    transporter_plate = models.CharField(_("Transporter Plate"), max_length=20, blank=True)

    class Meta:
        abstract = True


def bundle_path(instance, _):
    now = timezone.now()
    transporter_plate = "".join(instance.transporter_plate.split())
    return f"bundles/{now.year}/{now.month}/{now.day}/{now.year}{now.month}{now.day}_{now.hour}{now.minute}_{instance.company_siret}_{transporter_plate}.zip"


class PdfBundle(Base):
    class RequestTypeChoice(models.TextChoices):
        ROAD_CONTROL = "ROAD_CONTROL", _("Road control")
        BSD = "BSD", _("Bsd")

    class BundleChoice(models.TextChoices):
        INITIAL = "INITIAL", _("Initial")
        PROCESSING = "PROCESSING", _("Processing")
        READY = "READY", _("Ready")
        ERROR = "ERROR", _("Error")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    params = models.JSONField(default=dict)

    state = models.CharField(
        _("State"),
        max_length=20,
        choices=BundleChoice.choices,
        default=BundleChoice.INITIAL,
    )
    created_at = models.DateTimeField(_("Downloaded at"), default=timezone.now)
    created_by = models.ForeignKey(
        User, verbose_name=_("Created by"), on_delete=models.SET_NULL, blank=True, null=True
    )
    zip_file = models.FileField(
        _("Zip File"), upload_to=bundle_path, blank=True, max_length=512, storage=storages["private_s3"]
    )
    request_type = models.CharField(
        _("Request Type"), max_length=20, default=RequestTypeChoice.ROAD_CONTROL, choices=RequestTypeChoice.choices
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
        return f"Archive {self.company_siret} {self.created_at.strftime('%d %M %Y')}"


def bsd_path(instance, _):
    now = timezone.now()
    return f"bsds/{now.year}/{now.month}/{now.day}/bsd-{instance.id}.pdf"


class BsdPdfManager(models.Manager):
    def road_control(self):
        """Pdf created from raod control queries"""
        return self.filter(request_type="ROAD_CONTROL")

    def bsd(self):
        """Pdf created from individual pdf queries"""

        return self.filter(request_type="BSD")


class BsdPdf(Base):
    class RequestTypeChoice(models.TextChoices):
        ROAD_CONTROL = "ROAD_CONTROL", _("Road control")
        BSD = "BSD", _("Bsd")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bsd_id = models.CharField(_("Bsd Id "), max_length=30)
    packagings = models.CharField(_("Packagings"), max_length=255, blank=True)
    waste_code = models.CharField(_("Waste Code"), max_length=128, blank=True)
    weight = models.DecimalField(_("Weight"), max_digits=12, decimal_places=2, null=True, blank=True)
    adr_code = models.CharField(_("Adr Code"), max_length=255, blank=True)
    created_at = models.DateTimeField(_("Created at"), default=timezone.now)
    pdf_file = models.FileField(
        _("Pdf"), upload_to=bsd_path, blank=True, max_length=512, storage=storages["private_s3"]
    )

    created_by = models.ForeignKey(
        User, verbose_name=_("Created by"), on_delete=models.SET_NULL, blank=True, null=True
    )
    bundle = models.ForeignKey(
        PdfBundle, verbose_name=_("Bundle"), blank=True, null=True, on_delete=models.CASCADE, related_name="pdfs"
    )
    request_type = models.CharField(
        _("Request Type"), max_length=20, default=RequestTypeChoice.ROAD_CONTROL, choices=RequestTypeChoice.choices
    )
    objects = BsdPdfManager()

    class Meta:
        verbose_name = _("Pdf Bsd")
        verbose_name_plural = _("Pdfs Bsds")
        ordering = ("-created_at",)

        indexes = [
            models.Index(
                fields=[
                    "request_type",
                ]
            )
        ]

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
