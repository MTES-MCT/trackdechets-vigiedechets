from django.db import models
from django.utils.translation import gettext_lazy as _
from solo.models import SingletonModel


class BannerTypeChoice(models.TextChoices):
    INFO = "info", _("Info")
    WARNING = "warning", _("Warning")
    ALERT = "alert", _("Alert")


class SiteConfiguration(SingletonModel):
    banner_title = models.CharField(blank=True, verbose_name="Bannière d'information - titre")
    banner_content = models.TextField(blank=True, verbose_name="Bannière d'information - contenu")
    banner_type = models.CharField(
        verbose_name="Bannière d'information - type",
        max_length=20,
        choices=BannerTypeChoice.choices,
        default=BannerTypeChoice.INFO,
    )
    welcome_content = models.TextField(blank=True, verbose_name="Texte affiché sur le bandeau de la page d'accueil")
    welcome_content_connected = models.TextField(
        blank=True, verbose_name="Texte affiché sur le bandeau de la page d'accueil après connexion"
    )

    def __str__(self):
        return "Site Configuration"

    class Meta:
        verbose_name = "Site Configuration"
