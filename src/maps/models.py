import uuid

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CartoCompany(models.Model):
    siret = models.TextField(db_index=True)
    nom_etablissement = models.TextField(null=True, blank=True)

    profils = ArrayField(models.TextField(), null=True, blank=True)
    profils_collecteur = ArrayField(models.TextField(), null=True, blank=True)
    profils_installation = ArrayField(models.TextField(), null=True, blank=True)
    profils_installation_vhu = ArrayField(models.TextField(), null=True, blank=True)

    # Bsdd
    bsdd = models.BooleanField(null=True, blank=True)
    bsdd_emitter = models.BooleanField(default=False)
    bsdd_transporter = models.BooleanField(default=False)
    bsdd_destination = models.BooleanField(default=False)

    # Bsdnd
    bsdnd = models.BooleanField(null=True, blank=True)
    bsdnd_emitter = models.BooleanField(default=False)
    bsdnd_transporter = models.BooleanField(default=False)
    bsdnd_destination = models.BooleanField(default=False)

    # Bsda
    bsda = models.BooleanField(null=True, blank=True, db_index=True)
    bsda_emitter = models.BooleanField(default=False)
    bsda_transporter = models.BooleanField(default=False)
    bsda_destination = models.BooleanField(default=False)
    bsda_worker = models.BooleanField(default=False)

    # Bsff
    bsff = models.BooleanField(null=True, blank=True)
    bsff_emitter = models.BooleanField(default=False)
    bsff_transporter = models.BooleanField(default=False)
    bsff_destination = models.BooleanField(default=False)

    # Bsdasri
    bsdasri = models.BooleanField(null=True, blank=True)
    bsdasri_emitter = models.BooleanField(default=False)
    bsdasri_transporter = models.BooleanField(default=False)
    bsdasri_destination = models.BooleanField(default=False)

    # Bsvhu
    bsvhu = models.BooleanField(null=True, blank=True, db_index=True)
    bsvhu_emitter = models.BooleanField(default=False, db_index=True)
    bsvhu_transporter = models.BooleanField(default=False, db_index=True)
    bsvhu_destination = models.BooleanField(default=False, db_index=True)

    # Texs dd
    texs_dd = models.BooleanField(null=True, blank=True, db_index=True)
    texs_dd_emitter = models.BooleanField(default=False, db_index=True)
    texs_dd_transporter = models.BooleanField(default=False, db_index=True)
    texs_dd_destination = models.BooleanField(default=False, db_index=True)

    # Dnd
    dnd = models.BooleanField(null=True, blank=True, db_index=True)
    dnd_emitter = models.BooleanField(default=False, db_index=True)
    dnd_destination = models.BooleanField(default=False, db_index=True)

    # Texs
    texs = models.BooleanField(null=True, blank=True, db_index=True)
    texs_emitter = models.BooleanField(default=False, db_index=True)
    texs_destination = models.BooleanField(default=False, db_index=True)

    ssd = models.BooleanField(null=True, blank=True)
    pnttd = models.BooleanField(null=True, blank=True)

    processing_operations_bsdd = ArrayField(models.TextField(), null=True, blank=True)
    processing_operations_bsdnd = ArrayField(models.TextField(), null=True, blank=True)
    processing_operations_bsda = ArrayField(models.TextField(), null=True, blank=True)
    processing_operations_bsff = ArrayField(models.TextField(), null=True, blank=True)
    processing_operations_bsdasri = ArrayField(models.TextField(), null=True, blank=True)
    processing_operations_bsvhu = ArrayField(models.TextField(), null=True, blank=True)
    processing_operations_dnd = ArrayField(models.CharField(max_length=255), null=True, blank=True)
    processing_operations_texs = ArrayField(models.CharField(max_length=255), null=True, blank=True)

    # Waste codes fields
    waste_codes_bordereaux = ArrayField(models.CharField(max_length=255), null=True, blank=True)
    waste_codes_dnd_statements = ArrayField(models.CharField(max_length=255), null=True, blank=True)
    waste_codes_texs_statements = ArrayField(models.CharField(max_length=255), null=True, blank=True)
    waste_codes_processed = ArrayField(models.CharField(max_length=255), null=True, blank=True)

    code_commune_insee = models.CharField(max_length=255, null=True, blank=True)
    code_departement_insee = models.CharField(null=True, blank=True, db_index=True)
    code_region_insee = models.IntegerField(null=True, blank=True, db_index=True)

    adresse_td = models.TextField(null=True, blank=True)
    adresse_insee = models.TextField(null=True, blank=True)

    date_inscription = models.DateTimeField(null=True, blank=True)
    is_dormant = models.BooleanField(null=True, blank=True, db_index=True)
    coords = models.PointField(null=True, blank=True, spatial_index=True)

    class Meta:
        verbose_name = _("Établissement")
        verbose_name_plural = _("Établissements")
        indexes = [
            # BSDD indexes
            models.Index(fields=["bsdd", "bsdd_emitter"]),
            models.Index(fields=["bsdd", "bsdd_transporter"]),
            models.Index(fields=["bsdd", "bsdd_destination"]),
            # BSDA indexes
            models.Index(fields=["bsda", "bsda_emitter"]),
            models.Index(fields=["bsda", "bsda_transporter"]),
            models.Index(fields=["bsda", "bsda_destination"]),
            models.Index(fields=["bsda", "bsda_worker"]),
            # BSFF indexes
            models.Index(fields=["bsff", "bsff_emitter"]),
            models.Index(fields=["bsff", "bsff_transporter"]),
            models.Index(fields=["bsff", "bsff_destination"]),
            # BSDASRI indexes
            models.Index(fields=["bsdasri", "bsdasri_emitter"]),
            models.Index(fields=["bsdasri", "bsdasri_transporter"]),
            models.Index(fields=["bsdasri", "bsdasri_destination"]),
            # BSVHU indexes
            models.Index(fields=["bsvhu", "bsvhu_emitter"]),
            models.Index(fields=["bsvhu", "bsvhu_transporter"]),
            models.Index(fields=["bsvhu", "bsvhu_destination"]),
            # BSDND indexes
            models.Index(fields=["bsdnd", "bsdnd_emitter"]),
            models.Index(fields=["bsdnd", "bsdnd_transporter"]),
            models.Index(fields=["bsdnd", "bsdnd_destination"]),
            # TEXS_DD indexes
            models.Index(fields=["texs_dd", "texs_dd_emitter"]),
            models.Index(fields=["texs_dd", "texs_dd_transporter"]),
            models.Index(fields=["texs_dd", "texs_dd_destination"]),
            # DND indexes (no transporter role)
            models.Index(fields=["dnd", "dnd_emitter"]),
            models.Index(fields=["dnd", "dnd_destination"]),
            # TEXS indexes (no transporter role)
            models.Index(fields=["texs", "texs_emitter"]),
            models.Index(fields=["texs", "texs_destination"]),
            # Basic field indexes
            models.Index(fields=["siret"]),
            models.Index(fields=["code_departement_insee"]),
            models.Index(fields=["code_region_insee"]),
            # GIN indexes for all ArrayFields
            GinIndex(fields=["profils"]),
            GinIndex(fields=["profils_collecteur"]),
            GinIndex(fields=["profils_installation"]),
            GinIndex(fields=["profils_installation_vhu"]),
            GinIndex(fields=["processing_operations_bsdd"]),
            GinIndex(fields=["processing_operations_bsdnd"]),
            GinIndex(fields=["processing_operations_bsda"]),
            GinIndex(fields=["processing_operations_bsff"]),
            GinIndex(fields=["processing_operations_bsdasri"]),
            GinIndex(fields=["processing_operations_bsvhu"]),
            GinIndex(fields=["processing_operations_dnd"]),
            GinIndex(fields=["processing_operations_texs"]),
            GinIndex(fields=["waste_codes_bordereaux"]),
        ]
        constraints = [models.UniqueConstraint(fields=["siret"], name="unique_siret")]

    def __str__(self):
        return f"{self.siret} - {self.nom_etablissement}"

    @property
    def registered_on_td(self):
        return bool(self.date_inscription)


class BaseComputation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.PositiveSmallIntegerField(default=2023)
    created = models.DateTimeField(_("Created"), default=timezone.now)
    rubrique = models.TextField()
    quantite_autorisee = models.FloatField(
        null=True,
    )
    taux_consommation = models.FloatField(null=True)
    cumul_quantite_traitee = models.FloatField(null=True)
    moyenne_quantite_journaliere_traitee = models.FloatField(null=True)
    graph = models.JSONField(default=dict, null=True)

    class Meta:
        abstract = True


class DepartementsComputation(BaseComputation):
    code_departement_insee = models.TextField()
    nom_departement = models.TextField()
    code_region_insee = models.TextField()
    nombre_installations = models.FloatField(default=0)

    class Meta:
        verbose_name = _("Department Computation")
        verbose_name_plural = _("Department Computations")
        ordering = ("-created",)

        indexes = [
            models.Index(fields=["year", "rubrique"]),
            models.Index(fields=["year", "rubrique", "code_departement_insee"]),
        ]


class RegionsComputation(BaseComputation):
    code_region_insee = models.TextField()
    nom_region = models.TextField()
    nombre_installations = models.FloatField(default=0)

    class Meta:
        verbose_name = _("Regions Computation")
        verbose_name_plural = _("Regions Computations")
        ordering = ("-created",)

        indexes = [
            models.Index(fields=["year", "rubrique"]),
            models.Index(fields=["year", "rubrique", "code_region_insee"]),
        ]


class FranceComputation(BaseComputation):
    nombre_installations = models.FloatField(default=0)

    class Meta:
        verbose_name = _("France Computation")
        verbose_name_plural = _("France Computations")
        ordering = ("-created",)

        indexes = [
            models.Index(fields=["year", "rubrique"]),
        ]


class InstallationsComputation(BaseComputation):
    code_aiot = models.TextField(null=False)

    raison_sociale = models.TextField(
        null=True,
    )
    siret = models.TextField(null=True)
    adresse1 = models.TextField(
        null=True,
    )
    adresse2 = models.TextField(
        null=True,
    )
    code_postal = models.TextField(
        null=True,
    )
    commune = models.TextField(
        null=True,
    )
    etat_activite = models.TextField(
        null=True,
    )
    regime = models.TextField(
        null=True,
    )

    unite = models.TextField(
        null=True,
    )
    latitude = models.FloatField(null=True, default=None)
    longitude = models.FloatField(null=True, default=None)

    class Meta:
        verbose_name = _("Installations Computation")
        verbose_name_plural = _("Installations Computations")
        ordering = ("-created",)

        indexes = [
            models.Index(fields=["year", "rubrique"]),
            models.Index(fields=["year", "rubrique", "code_aiot"]),
        ]
