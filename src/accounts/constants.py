from django.db import models
from django.utils.translation import gettext_lazy as _


class UserCategoryChoice(models.TextChoices):
    STAFF_TD = "STAFF_TD", _("Staff Trackdéchets")
    ADMINISTRATION_CENTRALE = "ADMINISTRATION_CENTRALE", _("Administration centrale")
    INSPECTEUR_ICPE = "INSPECTEUR_ICPE", _("Inspecteur ICPE")
    CTT = "CTT", _("CTT - Contrôleur des transports routiers")
    INSPECTION_TRAVAIL = "INSPECTION_TRAVAIL", _("Inspection du travail")
    GENDARMERIE = "GENDARMERIE", _("Gendarmerie")
    ARS = "ARS", _("ARS")
    DOUANE = "DOUANE", _("Douane")
    OBSERVATOIRE = "OBSERVATOIRE", _("Observatoire")


ALL_USER_CATEGORIES = [
    UserCategoryChoice.STAFF_TD,
    UserCategoryChoice.ADMINISTRATION_CENTRALE,
    UserCategoryChoice.INSPECTEUR_ICPE,
    UserCategoryChoice.CTT,
    UserCategoryChoice.INSPECTION_TRAVAIL,
    UserCategoryChoice.GENDARMERIE,
    UserCategoryChoice.ARS,
    UserCategoryChoice.DOUANE,
    UserCategoryChoice.OBSERVATOIRE,
]

PERMS_SHEET_AND_REGISTRY = [
    UserCategoryChoice.STAFF_TD,
    UserCategoryChoice.ADMINISTRATION_CENTRALE,
    UserCategoryChoice.INSPECTEUR_ICPE,
    UserCategoryChoice.CTT,
    UserCategoryChoice.INSPECTION_TRAVAIL,
    UserCategoryChoice.GENDARMERIE,
    UserCategoryChoice.ARS,
    UserCategoryChoice.DOUANE,
]
PERMS_ROAD_CONTROL = [
    UserCategoryChoice.STAFF_TD,
    UserCategoryChoice.ADMINISTRATION_CENTRALE,
    UserCategoryChoice.INSPECTEUR_ICPE,
    UserCategoryChoice.CTT,
    UserCategoryChoice.GENDARMERIE,
    UserCategoryChoice.DOUANE,
]
PERMS_BSD_SEARCH = [
    UserCategoryChoice.STAFF_TD,
    UserCategoryChoice.ADMINISTRATION_CENTRALE,
    UserCategoryChoice.INSPECTEUR_ICPE,
    UserCategoryChoice.CTT,
    UserCategoryChoice.GENDARMERIE,
    UserCategoryChoice.DOUANE,
    UserCategoryChoice.INSPECTION_TRAVAIL,
    UserCategoryChoice.ARS,
]
PERMS_MAP = [
    UserCategoryChoice.STAFF_TD,
    UserCategoryChoice.ADMINISTRATION_CENTRALE,
    UserCategoryChoice.INSPECTEUR_ICPE,
    UserCategoryChoice.CTT,
    UserCategoryChoice.INSPECTION_TRAVAIL,
    UserCategoryChoice.GENDARMERIE,
    UserCategoryChoice.ARS,
    UserCategoryChoice.DOUANE,
    UserCategoryChoice.OBSERVATOIRE,
]
PERMS_MAP_ICPE = [
    UserCategoryChoice.STAFF_TD,
    UserCategoryChoice.ADMINISTRATION_CENTRALE,
    UserCategoryChoice.INSPECTEUR_ICPE,
    UserCategoryChoice.GENDARMERIE,
]

PERMS_DATA_EXPORT = [
    UserCategoryChoice.STAFF_TD,
    UserCategoryChoice.ADMINISTRATION_CENTRALE,
    UserCategoryChoice.OBSERVATOIRE,
]
PERMS_SENTINEL = [
    UserCategoryChoice.STAFF_TD,
    UserCategoryChoice.ADMINISTRATION_CENTRALE,
    UserCategoryChoice.INSPECTEUR_ICPE,
    UserCategoryChoice.GENDARMERIE,
    UserCategoryChoice.DOUANE,
]

PERMS_DASHBOARD = [
    UserCategoryChoice.STAFF_TD,
    UserCategoryChoice.ADMINISTRATION_CENTRALE,
]


class UserTypeChoice(models.TextChoices):
    HUMAN = "HUMAN", _("Human")
    API = "API", _("api")


MONAIOT = "MONAIOT"
PROCONNECT = "PROCONNECT"


class OIDCTypeChoice(models.TextChoices):
    MONAIOT = MONAIOT, _("MonAIOT")
    PROCONNECT = PROCONNECT, _("Proconnect")
