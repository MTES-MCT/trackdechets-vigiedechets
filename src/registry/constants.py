from django.db import models

REGISTRY_TYPE_ALL = "ALL"
REGISTRY_TYPE_INCOMING = "INCOMING"
REGISTRY_TYPE_OUTGOING = "OUTGOING"
REGISTRY_TYPE_TRANSPORTED = "TRANSPORTED"
REGISTRY_FORMAT_CSV = "csv"
REGISTRY_FORMAT_XLS = "xls"
WASTE_DND = "DND"
WASTE_ND = "DD"
WASTE_TEXS = "TEXS"


class RegistryV2Format(models.TextChoices):
    CSV = "CSV", "Texte (.csv)"
    XLSX = "XLSX", "Excel (.xlsx)"


class RegistryV2ExportState(models.TextChoices):
    """State options for processing tasks."""

    PENDING = "PENDING", "En attente"
    STARTED = "STARTED", "En cours"
    SUCCESSFUL = "SUCCESSFUL", "Terminé"
    FAILED = "FAILED", "Erreur"
    CANCELED = "CANCELED", "Annulé"


class RegistryV2ExportType(models.TextChoices):
    """Export types for registry v2."""

    # Registre exhaustif.
    # Registre qui n'est pas réglementaire et qui est indépendant des autres registres. Il permet
    # d'exporter un nombre d'informations conséquent sur l'ensemble des bordereaux sur lesquels un
    # acteur a été visé à partir du moment où l'enlèvement a été signé. Dans cet export, les bordereaux
    # sont triés par date d'enlèvement du déchet.
    # ALL = "ALL", "Registre exhaustif"

    # Registre entrant.
    # Registre réglementaire, les déchets apparaissent à partir du moment où l'enlèvement
    # a été signé et sont triés par date de réception du déchet.
    # https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000043884574
    INCOMING = "INCOMING", "Registre entrant"

    # Registre de gestion.
    # Registre réglementaire, les déchets apparaissent à partir du moment où l'enlèvement
    # a été signé et sont triés par date d'enlèvement du déchet (la date d'acquisition ou
    # de début de gestion du déchet n'apparaissant pas sur les bordereaux de suivi de déchet,
    # il n'est pas possible de trier le registre suivant cette date).
    # https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000043884599
    MANAGED = "MANAGED", "Registre des courtiers/négociants"

    # Registre sortant.
    # Registre réglementaire, les déchets apparaissent à partir du moment où l'enlèvement
    # a été signé et sont triés par date d'enlèvement du déchet.
    # https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000043884583
    OUTGOING = "OUTGOING", "Registre sortant"

    # Registre Sortie de statut de déchet.
    SSD = "SSD", "Registre Sortie de statut de déchet"

    # Registre de transport.
    # Registre réglementaire, les déchets apparaissent à partir du moment où l'enlèvement
    # a été signé et sont triés par date d'enlèvement du déchet.
    # https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000043884592
    TRANSPORTED = "TRANSPORTED", "Registre des transporteurs"


class RegistryV2DeclarationType(models.TextChoices):
    """Types of declarations."""

    # Tous types
    ALL = "ALL", "Tous"

    # Bordereau
    BSD = "BSD", "Tracé (bordereaux)"

    # Registre
    REGISTRY = "REGISTRY", "Déclaré (registre national)"


class RegistryV2WasteCode(models.TextChoices):
    WASTE_01_01_01 = "01 01 01", "01 01 01 - déchets provenant de l'extraction des minéraux métallifères"
    WASTE_01_01_02 = "01 01 02", "01 01 02 - déchets provenant de l'extraction des minéraux non métallifères"
    WASTE_01_03_04 = "01 03 04*", "01 03 04* - stériles acidogènes provenant de la transformation du sulfure"
    WASTE_01_03_05 = "01 03 05*", "01 03 05* - autres stériles contenant des substances dangereuses"
    WASTE_01_03_06 = "01 03 06", "01 03 06 - stériles autres que ceux visés aux rubriques 01 03 04 et 01 03 05"
    WASTE_01_03_07 = (
        "01 03 07*",
        "01 03 07* - autres déchets contenant des substances dangereuses provenant de la transformation physique et chimique des minéraux métallifères",
    )
    WASTE_01_03_08 = (
        "01 03 08",
        "01 03 08 - déchets de poussières et de poudres autres que ceux visés à la rubrique 01 03 07",
    )
    WASTE_01_03_09 = (
        "01 03 09",
        "01 03 09 - boues rouges issues de la production d'alumine autres que celles visées à la rubrique 01 03 10",
    )
    WASTE_01_03_10 = (
        "01 03 10*",
        "01 03 10* - boues rouges issues de la production d'alumine contenant des substances dangereuses, autres que les déchets visés à la rubrique 01 03 07",
    )
    WASTE_01_03_99 = "01 03 99", "01 03 99 - déchets non spécifiés ailleurs"
    WASTE_01_04_07 = (
        "01 04 07*",
        "01 04 07* - déchets contenant des substances dangereuses provenant de la transformation physique et chimique des minéraux non métallifères",
    )
    WASTE_01_04_08 = (
        "01 04 08",
        "01 04 08 - déchets de graviers et débris de pierres autres que ceux visés à la rubrique 01 04 07",
    )
    WASTE_01_04_09 = "01 04 09", "01 04 09 - déchets de sable et d'argile"
    WASTE_01_04_10 = (
        "01 04 10",
        "01 04 10 - déchets de poussières et de poudres autres que ceux visés à la rubrique 01 04 07",
    )
    WASTE_01_04_11 = (
        "01 04 11",
        "01 04 11 - déchets de la transformation de la potasse et des sels minéraux autres que ceux visés à la rubrique 01 04 07",
    )
    WASTE_01_04_12 = (
        "01 04 12",
        "01 04 12 - stériles et autres déchets provenant du lavage et du nettoyage des minéraux autres que ceux visés aux rubriques 01 04 07 et 01 04 11",
    )
    WASTE_01_04_13 = (
        "01 04 13",
        "01 04 13 - déchets provenant de la taille et du sciage des pierres autres que ceux visés à la rubrique 01 04 07",
    )
    WASTE_01_04_99 = "01 04 99", "01 04 99 - déchets non spécifiés ailleurs"
    WASTE_01_05_04 = "01 05 04", "01 05 04 - boues et autres déchets de forage à l'eau douce"
    WASTE_01_05_05 = "01 05 05*", "01 05 05* - boues et autres déchets de forage contenant des hydrocarbures"
    WASTE_01_05_06 = (
        "01 05 06*",
        "01 05 06* - boues de forage et autres déchets de forage contenant des substances dangereuses",
    )
    WASTE_01_05_07 = (
        "01 05 07",
        "01 05 07 - boues et autres déchets de forage contenant des sels de baryum, autres que ceux visés aux rubriques 01 05 05 et 01 05 06",
    )
    WASTE_01_05_08 = (
        "01 05 08",
        "01 05 08 - boues et autres déchets de forage contenant des chlorures, autres que ceux visés aux rubriques 01 05 05 et 01 05 06",
    )
    WASTE_01_05_99 = "01 05 99", "01 05 99 - déchets non spécifiés ailleurs"
    WASTE_02_01_01 = "02 01 01", "02 01 01 - boues provenant du lavage et du nettoyage"
    WASTE_02_01_02 = "02 01 02", "02 01 02 - déchets de tissus animaux"
    WASTE_02_01_03 = "02 01 03", "02 01 03 - déchets de tissus végétaux"
    WASTE_02_01_04 = "02 01 04", "02 01 04 - déchets de matières plastiques (à l'exclusion des emballages)"
    WASTE_02_01_06 = (
        "02 01 06",
        "02 01 06 - fèces, urine et fumier (y compris paille souillée), effluents, collectés séparément et traités hors site",
    )
    WASTE_02_01_07 = "02 01 07", "02 01 07 - déchets provenant de la sylviculture"
    WASTE_02_01_08 = "02 01 08*", "02 01 08* - déchets agrochimiques contenant des substances dangereuses"
    WASTE_02_01_09 = "02 01 09", "02 01 09 - déchets agrochimiques autres que ceux visés à la rubrique 02 01 08"
    WASTE_02_01_10 = "02 01 10", "02 01 10 - déchets métalliques"
    WASTE_02_01_99 = "02 01 99", "02 01 99 - déchets non spécifiés ailleurs"
    WASTE_02_02_01 = "02 02 01", "02 02 01 - boues provenant du lavage et du nettoyage"
    WASTE_02_02_02 = "02 02 02", "02 02 02 - déchets de tissus animaux"
    WASTE_02_02_03 = "02 02 03", "02 02 03 - matières impropres à la consommation ou à la transformation"
    WASTE_02_02_04 = "02 02 04", "02 02 04 - boues provenant du traitement in situ des effluents"
    WASTE_02_02_99 = "02 02 99", "02 02 99 - déchets non spécifiés ailleurs"
    WASTE_02_03_01 = (
        "02 03 01",
        "02 03 01 - boues provenant du lavage, du nettoyage, de l'épluchage, de la centrifugation et de la séparation",
    )
    WASTE_02_03_02 = "02 03 02", "02 03 02 - déchets d'agents de conservation"
    WASTE_02_03_03 = "02 03 03", "02 03 03 - déchets de l'extraction aux solvants"
    WASTE_02_03_04 = "02 03 04", "02 03 04 - matières impropres à la consommation ou à la transformation"
    WASTE_02_03_05 = "02 03 05", "02 03 05 - boues provenant du traitement in situ des effluents"
    WASTE_02_03_99 = "02 03 99", "02 03 99 - déchets non spécifiés ailleurs"
    WASTE_02_04_01 = "02 04 01", "02 04 01 - terre provenant du lavage et du nettoyage des betteraves"
    WASTE_02_04_02 = "02 04 02", "02 04 02 - carbonate de calcium déclassé"
    WASTE_02_04_03 = "02 04 03", "02 04 03 - boues provenant du traitement in situ des effluents"
    WASTE_02_04_99 = "02 04 99", "02 04 99 - déchets non spécifiés ailleurs"
    WASTE_02_05_01 = "02 05 01", "02 05 01 - matières impropres à la consommation ou à la transformation"
    WASTE_02_05_02 = "02 05 02", "02 05 02 - boues provenant du traitement in situ des effluents"
    WASTE_02_05_99 = "02 05 99", "02 05 99 - déchets non spécifiés ailleurs"
    WASTE_02_06_01 = "02 06 01", "02 06 01 - matières impropres à la consommation ou à la transformation"
    WASTE_02_06_02 = "02 06 02", "02 06 02 - déchets d'agents de conservation"
    WASTE_02_06_03 = "02 06 03", "02 06 03 - boues provenant du traitement in situ des effluents"
    WASTE_02_06_99 = "02 06 99", "02 06 99 - déchets non spécifiés ailleurs"
    WASTE_02_07_01 = (
        "02 07 01",
        "02 07 01 - déchets provenant du lavage, du nettoyage et de la réduction mécanique des matières premières",
    )
    WASTE_02_07_02 = "02 07 02", "02 07 02 - déchets de la distillation de l'alcool"
    WASTE_02_07_03 = "02 07 03", "02 07 03 - déchets de traitements chimiques"
    WASTE_02_07_04 = "02 07 04", "02 07 04 - matières impropres à la consommation ou à la transformation"
    WASTE_02_07_05 = "02 07 05", "02 07 05 - boues provenant du traitement in situ des effluents"
    WASTE_02_07_99 = "02 07 99", "02 07 99 - déchets non spécifiés ailleurs"
    WASTE_03_01_01 = "03 01 01", "03 01 01 - déchets d'écorce et de liège"
    WASTE_03_01_04 = (
        "03 01 04*",
        "03 01 04* - sciure de bois, copeaux, chutes, bois, panneaux de particules et placages contenant des substances dangereuses",
    )
    WASTE_03_01_05 = (
        "03 01 05",
        "03 01 05 - sciure de bois, copeaux, chutes, bois, panneaux de particules et placages autres que ceux visés à la rubrique 03 01 04",
    )
    WASTE_03_01_99 = "03 01 99", "03 01 99 - déchets non spécifiés ailleurs"
    WASTE_03_02_01 = "03 02 01*", "03 02 01* - composés organiques non halogénés de protection du bois"
    WASTE_03_02_02 = "03 02 02*", "03 02 02* - composés organochlorés de protection du bois"
    WASTE_03_02_03 = "03 02 03*", "03 02 03* - composés organométalliques de protection du bois"
    WASTE_03_02_04 = "03 02 04*", "03 02 04* - composés inorganiques de protection du bois"
    WASTE_03_02_05 = (
        "03 02 05*",
        "03 02 05* - autres produits de protection du bois contenant des substances dangereuses",
    )
    WASTE_03_02_99 = "03 02 99", "03 02 99 - produits de protection du bois non spécifiés ailleurs"
    WASTE_03_03_01 = "03 03 01", "03 03 01 - déchets d'écorce et de bois"
    WASTE_03_03_02 = "03 03 02", "03 03 02 - liqueurs vertes (provenant de la récupération de liqueur de cuisson)"
    WASTE_03_03_05 = "03 03 05", "03 03 05 - boues de désencrage provenant du recyclage du papier"
    WASTE_03_03_07 = (
        "03 03 07",
        "03 03 07 - refus séparés mécaniquement provenant du broyage de déchets de papier et de carton",
    )
    WASTE_03_03_08 = "03 03 08", "03 03 08 - déchets provenant du tri de papier et de carton destinés au recyclage"
    WASTE_03_03_09 = "03 03 09", "03 03 09 - déchets de boues résiduaires de chaux"
    WASTE_03_03_10 = (
        "03 03 10",
        "03 03 10 - refus fibreux, boues de fibres, de charge et de couchage provenant d'une séparation mécanique",
    )
    WASTE_03_03_11 = (
        "03 03 11",
        "03 03 11 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 03 03 10",
    )
    WASTE_03_03_99 = "03 03 99", "03 03 99 - déchets non spécifiés ailleurs"
    WASTE_04_01_01 = "04 01 01", "04 01 01 - déchets d'écharnage et refentes"
    WASTE_04_01_02 = "04 01 02", "04 01 02 - résidus de pelanage"
    WASTE_04_01_03 = "04 01 03*", "04 01 03* - déchets de dégraissage contenant des solvants sans phase liquide"
    WASTE_04_01_04 = "04 01 04", "04 01 04 - liqueur de tannage contenant du chrome"
    WASTE_04_01_05 = "04 01 05", "04 01 05 - liqueur de tannage sans chrome"
    WASTE_04_01_06 = (
        "04 01 06",
        "04 01 06 - boues, notamment provenant du traitement in situ des effluents, contenant du chrome",
    )
    WASTE_04_01_07 = (
        "04 01 07",
        "04 01 07 - boues, notamment provenant du traitement in situ des effluents, sans chrome",
    )
    WASTE_04_01_08 = (
        "04 01 08",
        "04 01 08 - déchets de cuir tanné (refentes sur bleu, dérayures, échantillonnages, poussières de ponçage), contenant du chrome",
    )
    WASTE_04_01_09 = "04 01 09", "04 01 09 - déchets provenant de l'habillage et des finitions"
    WASTE_04_01_99 = "04 01 99", "04 01 99 - déchets non spécifiés ailleurs"
    WASTE_04_02_09 = "04 02 09", "04 02 09 - matériaux composites (textile imprégné, élastomère, plastomère)"
    WASTE_04_02_10 = (
        "04 02 10",
        "04 02 10 - matières organiques issues de produits naturels (par exemple graisse, cire)",
    )
    WASTE_04_02_14 = "04 02 14*", "04 02 14* - déchets provenant des finitions contenant des solvants organiques"
    WASTE_04_02_15 = (
        "04 02 15",
        "04 02 15 - déchets provenant des finitions autres que ceux visés à la rubrique 04 02 14",
    )
    WASTE_04_02_16 = "04 02 16*", "04 02 16* - teintures et pigments contenant des substances dangereuses"
    WASTE_04_02_17 = "04 02 17", "04 02 17 - teintures et pigments autres que ceux visés à la rubrique 04 02 16"
    WASTE_04_02_19 = (
        "04 02 19*",
        "04 02 19* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_04_02_20 = (
        "04 02 20",
        "04 02 20 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 04 02 19",
    )
    WASTE_04_02_21 = "04 02 21", "04 02 21 - fibres textiles non ouvrées"
    WASTE_04_02_22 = "04 02 22", "04 02 22 - fibres textiles ouvrées"
    WASTE_04_02_99 = "04 02 99", "04 02 99 - déchets non spécifiés ailleurs"
    WASTE_05_01_02 = "05 01 02*", "05 01 02* - boues de dessalage"
    WASTE_05_01_03 = "05 01 03*", "05 01 03* - boues de fond de cuves"
    WASTE_05_01_04 = "05 01 04*", "05 01 04* - boues d'alkyles acides"
    WASTE_05_01_05 = "05 01 05*", "05 01 05* - hydrocarbures accidentellement répandus"
    WASTE_05_01_06 = (
        "05 01 06*",
        "05 01 06* - boues contenant des hydrocarbures provenant des opérations de maintenance de l'installation ou des équipements",
    )
    WASTE_05_01_07 = "05 01 07*", "05 01 07* - goudrons acides"
    WASTE_05_01_08 = "05 01 08*", "05 01 08* - autres goudrons"
    WASTE_05_01_09 = (
        "05 01 09*",
        "05 01 09* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_05_01_10 = (
        "05 01 10",
        "05 01 10 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 05 01 09",
    )
    WASTE_05_01_11 = "05 01 11*", "05 01 11* - déchets provenant du nettoyage d'hydrocarbures avec des bases"
    WASTE_05_01_12 = "05 01 12*", "05 01 12* - hydrocarbures contenant des acides"
    WASTE_05_01_13 = "05 01 13", "05 01 13 - boues du traitement de l'eau d'alimentation des chaudières"
    WASTE_05_01_14 = "05 01 14", "05 01 14 - déchets provenant des colonnes de refroidissement"
    WASTE_05_01_15 = "05 01 15*", "05 01 15* - argiles de filtration usées"
    WASTE_05_01_16 = "05 01 16", "05 01 16 - déchets contenant du soufre provenant de la désulfuration du pétrole"
    WASTE_05_01_17 = "05 01 17", "05 01 17 - mélanges bitumineux"
    WASTE_05_01_99 = "05 01 99", "05 01 99 - déchets non spécifiés ailleurs"
    WASTE_05_06_01 = "05 06 01*", "05 06 01* - goudrons acides"
    WASTE_05_06_03 = "05 06 03*", "05 06 03* - autres goudrons"
    WASTE_05_06_04 = "05 06 04", "05 06 04 - déchets provenant des colonnes de refroidissement"
    WASTE_05_06_99 = "05 06 99", "05 06 99 - déchets non spécifiés ailleurs"
    WASTE_05_07_01 = "05 07 01*", "05 07 01* - déchets contenant du mercure"
    WASTE_05_07_02 = "05 07 02", "05 07 02 - déchets contenant du soufre"
    WASTE_05_07_99 = "05 07 99", "05 07 99 - déchets non spécifiés ailleurs"
    WASTE_06_01_01 = "06 01 01*", "06 01 01* - acide sulfurique et acide sulfureux"
    WASTE_06_01_02 = "06 01 02*", "06 01 02* - acide chlorhydrique"
    WASTE_06_01_03 = "06 01 03*", "06 01 03* - acide fluorhydrique"
    WASTE_06_01_04 = "06 01 04*", "06 01 04* - acide phosphorique et acide phosphoreux"
    WASTE_06_01_05 = "06 01 05*", "06 01 05* - acide nitrique et acide nitreux"
    WASTE_06_01_06 = "06 01 06*", "06 01 06* - autres acides"
    WASTE_06_01_99 = "06 01 99", "06 01 99 - déchets non spécifiés ailleurs"
    WASTE_06_02_01 = "06 02 01*", "06 02 01* - hydroxyde de calcium"
    WASTE_06_02_03 = "06 02 03*", "06 02 03* - hydroxyde d'ammonium"
    WASTE_06_02_04 = "06 02 04*", "06 02 04* - hydroxyde de sodium et hydroxyde de potassium"
    WASTE_06_02_05 = "06 02 05*", "06 02 05* - autres bases"
    WASTE_06_02_99 = "06 02 99", "06 02 99 - déchets non spécifiés ailleurs"
    WASTE_06_03_11 = "06 03 11*", "06 03 11* - sels et solutions contenant des cyanures"
    WASTE_06_03_13 = "06 03 13*", "06 03 13* - sels et solutions contenant des métaux lourds"
    WASTE_06_03_14 = (
        "06 03 14",
        "06 03 14 - sels solides et solutions autres que ceux visés aux rubriques 06 03 11 et 06 03 13",
    )
    WASTE_06_03_15 = "06 03 15*", "06 03 15* - oxydes métalliques contenant des métaux lourds"
    WASTE_06_03_16 = "06 03 16", "06 03 16 - oxydes métalliques autres que ceux visés à la rubrique 06 03 15"
    WASTE_06_03_99 = "06 03 99", "06 03 99 - déchets non spécifiés ailleurs"
    WASTE_06_04_03 = "06 04 03*", "06 04 03* - déchets contenant de l'arsenic"
    WASTE_06_04_04 = "06 04 04*", "06 04 04* - déchets contenant du mercure"
    WASTE_06_04_05 = "06 04 05*", "06 04 05* - déchets contenant d'autres métaux lourds"
    WASTE_06_04_99 = "06 04 99", "06 04 99 - déchets non spécifiés ailleurs"
    WASTE_06_05_02 = (
        "06 05 02*",
        "06 05 02* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_06_05_03 = (
        "06 05 03",
        "06 05 03 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 06 05 02",
    )
    WASTE_06_06_02 = "06 06 02*", "06 06 02* - déchets contenant des sulfures dangereux"
    WASTE_06_06_03 = (
        "06 06 03",
        "06 06 03 - déchets contenant des sulfures autres que ceux visés à la rubrique 06 06 02",
    )
    WASTE_06_06_99 = "06 06 99", "06 06 99 - déchets non spécifiés ailleurs"
    WASTE_06_07_01 = "06 07 01*", "06 07 01* - déchets contenant de l'amiante provenant de l'électrolyse"
    WASTE_06_07_02 = "06 07 02*", "06 07 02* - déchets de charbon actif utilisé pour la production du chlore"
    WASTE_06_07_03 = "06 07 03*", "06 07 03* - boues de sulfate de baryum contenant du mercure"
    WASTE_06_07_04 = "06 07 04*", "06 07 04* - solutions et acides, par exemple acide de contact"
    WASTE_06_07_99 = "06 07 99", "06 07 99 - déchets non spécifiés ailleurs"
    WASTE_06_08_02 = "06 08 02*", "06 08 02* - déchets contenant des chlorosilanes dangereux"
    WASTE_06_08_99 = "06 08 99", "06 08 99 - déchets non spécifiés ailleurs"
    WASTE_06_09_02 = "06 09 02", "06 09 02 - scories phosphoriques"
    WASTE_06_09_03 = (
        "06 09 03*",
        "06 09 03* - déchets de réactions basées sur le calcium contenant des substances dangereuses ou contaminées par de telles substances",
    )
    WASTE_06_09_04 = (
        "06 09 04",
        "06 09 04 - déchets de réactions basées sur le calcium autres que ceux visés à la rubrique 06 09 03",
    )
    WASTE_06_09_99 = "06 09 99", "06 09 99 - déchets non spécifiés ailleurs"
    WASTE_06_10_02 = "06 10 02*", "06 10 02* - déchets contenant des substances dangereuses"
    WASTE_06_10_99 = "06 10 99", "06 10 99 - déchets non spécifiés ailleurs"
    WASTE_06_11_01 = (
        "06 11 01",
        "06 11 01 - déchets de réactions basées sur le calcium provenant de la production de dioxyde de titane",
    )
    WASTE_06_11_99 = "06 11 99", "06 11 99 - déchets non spécifiés ailleurs"
    WASTE_06_13_01 = (
        "06 13 01*",
        "06 13 01* - produits phytosanitaires inorganiques, agents de protection du bois et autres biocides",
    )
    WASTE_06_13_02 = "06 13 02*", "06 13 02* - charbon actif usé (sauf rubrique 06 07 02)"
    WASTE_06_13_03 = "06 13 03", "06 13 03 - noir de carbone"
    WASTE_06_13_04 = "06 13 04*", "06 13 04* - déchets provenant de la transformation de l'amiante"
    WASTE_06_13_05 = "06 13 05*", "06 13 05* - suies"
    WASTE_06_13_99 = "06 13 99", "06 13 99 - déchets non spécifiés ailleurs"
    WASTE_07_01_01 = "07 01 01*", "07 01 01* - eaux de lavage et liqueurs mères aqueuses"
    WASTE_07_01_03 = "07 01 03*", "07 01 03* - solvants, liquides de lavage et liqueurs mères organiques halogénés"
    WASTE_07_01_04 = "07 01 04*", "07 01 04* - autres solvants, liquides de lavage et liqueurs mères organiques"
    WASTE_07_01_07 = "07 01 07*", "07 01 07* - résidus de réaction et résidus de distillation halogénés"
    WASTE_07_01_08 = "07 01 08*", "07 01 08* - autres résidus de réaction et résidus de distillation"
    WASTE_07_01_09 = "07 01 09*", "07 01 09* - gâteaux de filtration et absorbants usés halogénés"
    WASTE_07_01_10 = "07 01 10*", "07 01 10* - autres gâteaux de filtration et absorbants usés"
    WASTE_07_01_11 = (
        "07 01 11*",
        "07 01 11* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_07_01_12 = (
        "07 01 12",
        "07 01 12 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 07 01 11",
    )
    WASTE_07_01_99 = "07 01 99", "07 01 99 - déchets non spécifiés ailleurs"
    WASTE_07_02_01 = "07 02 01*", "07 02 01* - eaux de lavage et liqueurs mères aqueuses"
    WASTE_07_02_03 = "07 02 03*", "07 02 03* - solvants, liquides de lavage et liqueurs mères organiques halogénés"
    WASTE_07_02_04 = "07 02 04*", "07 02 04* - autres solvants, liquides de lavage et liqueurs mères organiques"
    WASTE_07_02_07 = "07 02 07*", "07 02 07* - résidus de réaction et résidus de distillation halogénés"
    WASTE_07_02_08 = "07 02 08*", "07 02 08* - autres résidus de réaction et résidus de distillation"
    WASTE_07_02_09 = "07 02 09*", "07 02 09* - gâteaux de filtration et absorbants usés halogénés"
    WASTE_07_02_10 = "07 02 10*", "07 02 10* - autres gâteaux de filtration et absorbants usés"
    WASTE_07_02_11 = (
        "07 02 11*",
        "07 02 11* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_07_02_12 = (
        "07 02 12",
        "07 02 12 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 07 02 11",
    )
    WASTE_07_02_13 = "07 02 13", "07 02 13 - déchets plastiques"
    WASTE_07_02_14 = "07 02 14*", "07 02 14* - déchets provenant d'additifs contenant des substances dangereuses"
    WASTE_07_02_15 = "07 02 15", "07 02 15 - déchets provenant d'additifs autres que ceux visés à la rubrique 07 02 14"
    WASTE_07_02_16 = "07 02 16*", "07 02 16* - déchets contenant des silicones dangereux"
    WASTE_07_02_17 = (
        "07 02 17",
        "07 02 17 - déchets contenant des silicones autres que ceux visés à la rubrique 07 02 16",
    )
    WASTE_07_02_99 = "07 02 99", "07 02 99 - déchets non spécifiés ailleurs"
    WASTE_07_03_01 = "07 03 01*", "07 03 01* - eaux de lavage et liqueurs mères aqueuses"
    WASTE_07_03_03 = "07 03 03*", "07 03 03* - solvants, liquides de lavage et liqueurs mères organiques halogénés"
    WASTE_07_03_04 = "07 03 04*", "07 03 04* - autres solvants, liquides de lavage et liqueurs mères organiques"
    WASTE_07_03_07 = "07 03 07*", "07 03 07* - résidus de réaction et résidus de distillation halogénés"
    WASTE_07_03_08 = "07 03 08*", "07 03 08* - autres résidus de réaction et résidus de distillation"
    WASTE_07_03_09 = "07 03 09*", "07 03 09* - gâteaux de filtration et absorbants usés halogénés"
    WASTE_07_03_10 = "07 03 10*", "07 03 10* - autres gâteaux de filtration et absorbants usés"
    WASTE_07_03_11 = (
        "07 03 11*",
        "07 03 11* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_07_03_12 = (
        "07 03 12",
        "07 03 12 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 07 03 11",
    )
    WASTE_07_03_99 = "07 03 99", "07 03 99 - déchets non spécifiés ailleurs"
    WASTE_07_04_01 = "07 04 01*", "07 04 01* - eaux de lavage et liqueurs mères aqueuses"
    WASTE_07_04_03 = "07 04 03*", "07 04 03* - solvants, liquides de lavage et liqueurs mères organiques halogénés"
    WASTE_07_04_04 = "07 04 04*", "07 04 04* - autres solvants, liquides de lavage et liqueurs mères organiques"
    WASTE_07_04_07 = "07 04 07*", "07 04 07* - résidus de réaction et résidus de distillation halogénés"
    WASTE_07_04_08 = "07 04 08*", "07 04 08* - autres résidus de réaction et résidus de distillation"
    WASTE_07_04_09 = "07 04 09*", "07 04 09* - gâteaux de filtration et absorbants usés halogénés"
    WASTE_07_04_10 = "07 04 10*", "07 04 10* - autres gâteaux de filtration et absorbants usés"
    WASTE_07_04_11 = (
        "07 04 11*",
        "07 04 11* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_07_04_12 = (
        "07 04 12",
        "07 04 12 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 07 04 11",
    )
    WASTE_07_04_13 = "07 04 13*", "07 04 13* - déchets solides contenant des substances dangereuses"
    WASTE_07_04_99 = "07 04 99", "07 04 99 - déchets non spécifiés ailleurs"
    WASTE_07_05_01 = "07 05 01*", "07 05 01* - eaux de lavage et liqueurs mères aqueuses"
    WASTE_07_05_03 = "07 05 03*", "07 05 03* - solvants, liquides de lavage et liqueurs mères organiques halogénés"
    WASTE_07_05_04 = "07 05 04*", "07 05 04* - autres solvants, liquides de lavage et liqueurs mères organiques"
    WASTE_07_05_07 = "07 05 07*", "07 05 07* - résidus de réaction et résidus de distillation halogénés"
    WASTE_07_05_08 = "07 05 08*", "07 05 08* - autres résidus de réaction et résidus de distillation"
    WASTE_07_05_09 = "07 05 09*", "07 05 09* - gâteaux de filtration et absorbants usés halogénés"
    WASTE_07_05_10 = "07 05 10*", "07 05 10* - autres gâteaux de filtration et absorbants usés"
    WASTE_07_05_11 = (
        "07 05 11*",
        "07 05 11* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_07_05_12 = (
        "07 05 12",
        "07 05 12 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 07 05 11",
    )
    WASTE_07_05_13 = "07 05 13*", "07 05 13* - déchets solides contenant des substances dangereuses"
    WASTE_07_05_14 = "07 05 14", "07 05 14 - déchets solides autres que ceux visés à la rubrique 07 05 13"
    WASTE_07_05_99 = "07 05 99", "07 05 99 - déchets non spécifiés ailleurs"
    WASTE_07_06_01 = "07 06 01*", "07 06 01* - eaux de lavage et liqueurs mères aqueuses"
    WASTE_07_06_03 = "07 06 03*", "07 06 03* - solvants, liquides de lavage et liqueurs mères organiques halogénés"
    WASTE_07_06_04 = "07 06 04*", "07 06 04* - autres solvants, liquides de lavage et liqueurs mères organiques"
    WASTE_07_06_07 = "07 06 07*", "07 06 07* - résidus de réaction et résidus de distillation halogénés"
    WASTE_07_06_08 = "07 06 08*", "07 06 08* - autres résidus de réaction et résidus de distillation"
    WASTE_07_06_09 = "07 06 09*", "07 06 09* - gâteaux de filtration et absorbants usés halogénés"
    WASTE_07_06_10 = "07 06 10*", "07 06 10* - autres gâteaux de filtration et absorbants usés"
    WASTE_07_06_11 = (
        "07 06 11*",
        "07 06 11* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_07_06_12 = (
        "07 06 12",
        "07 06 12 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 07 06 11",
    )
    WASTE_07_06_99 = "07 06 99", "07 06 99 - déchets non spécifiés ailleurs"
    WASTE_07_07_01 = "07 07 01*", "07 07 01* - eaux de lavage et liqueurs mères aqueuses"
    WASTE_07_07_03 = "07 07 03*", "07 07 03* - solvants, liquides de lavage et liqueurs mères organiques halogénés"
    WASTE_07_07_04 = "07 07 04*", "07 07 04* - autres solvants, liquides de lavage et liqueurs mères organiques"
    WASTE_07_07_07 = "07 07 07*", "07 07 07* - résidus de réaction et résidus de distillation halogénés"
    WASTE_07_07_08 = "07 07 08*", "07 07 08* - autres résidus de réaction et résidus de distillation"
    WASTE_07_07_09 = "07 07 09*", "07 07 09* - gâteaux de filtration et absorbants usés halogénés"
    WASTE_07_07_10 = "07 07 10*", "07 07 10* - autres gâteaux de filtration et absorbants usés"
    WASTE_07_07_11 = (
        "07 07 11*",
        "07 07 11* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_07_07_12 = (
        "07 07 12",
        "07 07 12 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 07 07 11",
    )
    WASTE_07_07_99 = "07 07 99", "07 07 99 - déchets non spécifiés ailleurs"
    WASTE_08_01_11 = (
        "08 01 11*",
        "08 01 11* - déchets de peintures et vernis contenant des solvants organiques ou d'autres substances dangereuses",
    )
    WASTE_08_01_12 = (
        "08 01 12",
        "08 01 12 - déchets de peintures ou vernis autres que ceux visés à la rubrique 08 01 11",
    )
    WASTE_08_01_13 = (
        "08 01 13*",
        "08 01 13* - boues provenant de peintures ou vernis contenant des solvants organiques ou autres substances dangereuses",
    )
    WASTE_08_01_14 = (
        "08 01 14",
        "08 01 14 - boues provenant de peintures ou vernis autres que celles visées à la rubrique 08 01 13",
    )
    WASTE_08_01_15 = (
        "08 01 15*",
        "08 01 15* - boues aqueuses contenant de la peinture ou du vernis contenant des solvants organiques ou autres substances dangereuses",
    )
    WASTE_08_01_16 = (
        "08 01 16",
        "08 01 16 - boues aqueuses contenant de la peinture ou du vernis autres que celles visées à la rubrique 08 01 15",
    )
    WASTE_08_01_17 = (
        "08 01 17*",
        "08 01 17* - déchets provenant du décapage de peintures ou vernis contenant des solvants organiques ou autres substances dangereuses",
    )
    WASTE_08_01_18 = (
        "08 01 18",
        "08 01 18 - déchets provenant du décapage de peintures ou vernis autres que ceux visés à la rubrique 08 01 17",
    )
    WASTE_08_01_19 = (
        "08 01 19*",
        "08 01 19* - boues aqueuses contenant de la peinture ou du vernis contenant des solvants organiques ou autres substances dangereuses",
    )
    WASTE_08_01_20 = (
        "08 01 20",
        "08 01 20 - suspensions aqueuses contenant de la peinture ou du vernis autres que celles visées à la rubrique 08 01 19",
    )
    WASTE_08_01_21 = "08 01 21*", "08 01 21* - déchets de décapants de peintures ou vernis"
    WASTE_08_01_99 = "08 01 99", "08 01 99 - déchets non spécifiés ailleurs"
    WASTE_08_02_01 = "08 02 01", "08 02 01 - déchets de produits de revêtement en poudre"
    WASTE_08_02_02 = "08 02 02", "08 02 02 - boues aqueuses contenant des matériaux céramiques"
    WASTE_08_02_03 = "08 02 03", "08 02 03 - suspensions aqueuses contenant des matériaux céramiques"
    WASTE_08_02_99 = "08 02 99", "08 02 99 - déchets non spécifiés ailleurs"
    WASTE_08_03_07 = "08 03 07", "08 03 07 - boues aqueuses contenant de l'encre"
    WASTE_08_03_08 = "08 03 08", "08 03 08 - déchets liquides aqueux contenant de l'encre"
    WASTE_08_03_12 = "08 03 12*", "08 03 12* - déchets d'encres contenant des substances dangereuses"
    WASTE_08_03_13 = "08 03 13", "08 03 13 - déchets d'encres autres que ceux visés à la rubrique 08 03 12"
    WASTE_08_03_14 = "08 03 14*", "08 03 14* - boues d'encre contenant des substances dangereuses"
    WASTE_08_03_15 = "08 03 15", "08 03 15 - boues d'encre autres que celles visées à la rubrique 08 03 14"
    WASTE_08_03_16 = "08 03 16*", "08 03 16* - déchets de solution de morsure"
    WASTE_08_03_17 = "08 03 17*", "08 03 17* - déchets de toner d'impression contenant des substances dangereuses"
    WASTE_08_03_18 = (
        "08 03 18",
        "08 03 18 - déchets de toner d'impression autres que ceux visés à la rubrique 08 03 17",
    )
    WASTE_08_03_19 = "08 03 19*", "08 03 19* - huiles dispersées"
    WASTE_08_03_99 = "08 03 99", "08 03 99 - déchets non spécifiés ailleurs"
    WASTE_08_04_09 = (
        "08 04 09*",
        "08 04 09* - déchets de colles et mastics contenant des solvants organiques ou d'autres substances dangereuses",
    )
    WASTE_08_04_10 = "08 04 10", "08 04 10 - déchets de colles et mastics autres que ceux visés à la rubrique 08 04 09"
    WASTE_08_04_11 = (
        "08 04 11*",
        "08 04 11* - boues de colles et mastics contenant des solvants organiques ou d'autres substances dangereuses",
    )
    WASTE_08_04_12 = (
        "08 04 12",
        "08 04 12 - boues de colles et mastics autres que celles visées à la rubrique 08 04 11",
    )
    WASTE_08_04_13 = (
        "08 04 13*",
        "08 04 13* - boues aqueuses contenant des colles ou mastics contenant des solvants organiques ou d'autres substances dangereuses",
    )
    WASTE_08_04_14 = (
        "08 04 14",
        "08 04 14 - boues aqueuses contenant des colles et mastics autres que celles visées à la rubrique 08 04 13",
    )
    WASTE_08_04_15 = (
        "08 04 15*",
        "08 04 15* - déchets liquides aqueux contenant des colles ou mastics contenant des solvants organiques ou d'autres substances dangereuses",
    )
    WASTE_08_04_16 = (
        "08 04 16",
        "08 04 16 - déchets liquides aqueux contenant des colles ou mastics autres que ceux visés à la rubrique 08 04 15",
    )
    WASTE_08_04_17 = "08 04 17*", "08 04 17* - huile de résine"
    WASTE_08_04_99 = "08 04 99", "08 04 99 - déchets non spécifiés ailleurs"
    WASTE_08_05_01 = "08 05 01*", "08 05 01* - déchets d'isocyanates"
    WASTE_09_01_01 = "09 01 01*", "09 01 01* - bains de développement aqueux contenant un activateur"
    WASTE_09_01_02 = "09 01 02*", "09 01 02* - bains de développement aqueux pour plaques offset"
    WASTE_09_01_03 = "09 01 03*", "09 01 03* - bains de développement contenant des solvants"
    WASTE_09_01_04 = "09 01 04*", "09 01 04* - bains de fixation"
    WASTE_09_01_05 = "09 01 05*", "09 01 05* - bains de blanchiment et bains de blanchiment/fixation"
    WASTE_09_01_06 = (
        "09 01 06*",
        "09 01 06* - déchets contenant de l'argent provenant du traitement in situ des déchets photographiques",
    )
    WASTE_09_01_07 = (
        "09 01 07",
        "09 01 07 - pellicules et papiers photographiques contenant de l'argent ou des composés de l'argent",
    )
    WASTE_09_01_08 = "09 01 08", "09 01 08 - pellicules et papiers photographiques sans argent ni composés de l'argent"
    WASTE_09_01_10 = "09 01 10", "09 01 10 - appareils photographiques à usage unique sans piles"
    WASTE_09_01_11 = (
        "09 01 11*",
        "09 01 11* - appareils photographiques à usage unique contenant des piles visées aux rubriques 16 06 01, 16 06 02 ou 16 06 03",
    )
    WASTE_09_01_12 = (
        "09 01 12",
        "09 01 12 - appareils photographiques à usage unique contenant des piles autres que ceux visés à la rubrique 09 01 11",
    )
    WASTE_09_01_13 = (
        "09 01 13*",
        "09 01 13* - déchets liquides aqueux provenant de la récupération in situ de l'argent autres que ceux visés à la rubrique 09 01 06",
    )
    WASTE_09_01_99 = "09 01 99", "09 01 99 - déchets non spécifiés ailleurs"
    WASTE_10_01_01 = (
        "10 01 01",
        "10 01 01 - mâchefers, scories et cendres sous chaudière (sauf cendres sous chaudière visées à la rubrique 10 01 04)",
    )
    WASTE_10_01_02 = "10 01 02", "10 01 02 - cendres volantes de charbon"
    WASTE_10_01_03 = "10 01 03", "10 01 03 - cendres volantes de tourbe et de bois non traité"
    WASTE_10_01_04 = "10 01 04*", "10 01 04* - cendres volantes et cendres sous chaudière d'hydrocarbures"
    WASTE_10_01_05 = (
        "10 01 05",
        "10 01 05 - déchets solides de réactions basées sur le calcium, provenant de la désulfuration des gaz de fumée",
    )
    WASTE_10_01_07 = (
        "10 01 07",
        "10 01 07 - boues de réactions basées sur le calcium, provenant de la désulfuration des gaz de fumée",
    )
    WASTE_10_01_09 = "10 01 09*", "10 01 09* - acide sulfurique"
    WASTE_10_01_13 = (
        "10 01 13*",
        "10 01 13* - cendres volantes provenant d'hydrocarbures émulsifiés employés comme combustibles",
    )
    WASTE_10_01_14 = (
        "10 01 14*",
        "10 01 14* - mâchefers, scories et cendres sous chaudière provenant de la coïncinération contenant des substances dangereuses",
    )
    WASTE_10_01_15 = (
        "10 01 15",
        "10 01 15 - mâchefers, scories et cendres sous chaudière provenant de la coïncinération autres que ceux visés à la rubrique 10 01 14",
    )
    WASTE_10_01_16 = (
        "10 01 16*",
        "10 01 16* - cendres volantes provenant de la coïncinération contenant des substances dangereuses",
    )
    WASTE_10_01_17 = (
        "10 01 17",
        "10 01 17 - cendres volantes provenant de la coïncinération autres que celles visées à la rubrique 10 01 16",
    )
    WASTE_10_01_18 = (
        "10 01 18*",
        "10 01 18* - déchets provenant de l'épuration des gaz contenant des substances dangereuses",
    )
    WASTE_10_01_19 = (
        "10 01 19",
        "10 01 19 - déchets provenant de l'épuration des gaz autres que ceux visés aux rubriques 10 01 05, 10 01 07 et 10 01 18",
    )
    WASTE_10_01_20 = (
        "10 01 20*",
        "10 01 20* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_10_01_21 = (
        "10 01 21",
        "10 01 21 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 10 01 20",
    )
    WASTE_10_01_22 = (
        "10 01 22*",
        "10 01 22* - boues aqueuses provenant du nettoyage des chaudières contenant des substances dangereuses",
    )
    WASTE_10_01_23 = (
        "10 01 23",
        "10 01 23 - boues aqueuses provenant du nettoyage des chaudières autres que celles visées à la rubrique 10 01 22",
    )
    WASTE_10_01_24 = "10 01 24", "10 01 24 - sables provenant de lits fluidisés"
    WASTE_10_01_25 = (
        "10 01 25",
        "10 01 25 - déchets provenant du stockage et de la préparation des combustibles des centrales à charbon",
    )
    WASTE_10_01_26 = "10 01 26", "10 01 26 - déchets provenant de l'épuration des eaux de refroidissement"
    WASTE_10_01_99 = "10 01 99", "10 01 99 - déchets non spécifiés ailleurs"
    WASTE_10_02_01 = "10 02 01", "10 02 01 - déchets de laitiers de hauts fourneaux et d'aciéries"
    WASTE_10_02_02 = "10 02 02", "10 02 02 - laitiers non traités"
    WASTE_10_02_07 = (
        "10 02 07*",
        "10 02 07* - déchets solides provenant de l'épuration des fumées contenant des substances dangereuses",
    )
    WASTE_10_02_08 = (
        "10 02 08",
        "10 02 08 - déchets solides provenant de l'épuration des fumées autres que ceux visés à la rubrique 10 02 07",
    )
    WASTE_10_02_10 = "10 02 10", "10 02 10 - battitures de laminoir"
    WASTE_10_02_11 = (
        "10 02 11*",
        "10 02 11* - déchets provenant de l'épuration des eaux de refroidissement contenant des hydrocarbures",
    )
    WASTE_10_02_12 = (
        "10 02 12",
        "10 02 12 - déchets provenant de l'épuration des eaux de refroidissement autres que ceux visés à la rubrique 10 02 11",
    )
    WASTE_10_02_13 = (
        "10 02 13*",
        "10 02 13* - boues et gâteaux de filtration provenant de l'épuration des fumées contenant des substances dangereuses",
    )
    WASTE_10_02_14 = (
        "10 02 14",
        "10 02 14 - boues et gâteaux de filtration provenant de l'épuration des fumées autres que ceux visés à la rubrique 10 02 13",
    )
    WASTE_10_02_15 = "10 02 15", "10 02 15 - autres boues et gâteaux de filtration"
    WASTE_10_02_99 = "10 02 99", "10 02 99 - déchets non spécifiés ailleurs"
    WASTE_10_03_02 = "10 03 02", "10 03 02 - déchets d'anodes"
    WASTE_10_03_04 = "10 03 04*", "10 03 04* - scories provenant de la production primaire"
    WASTE_10_03_05 = "10 03 05", "10 03 05 - déchets d'alumine"
    WASTE_10_03_08 = "10 03 08*", "10 03 08* - scories salées de seconde fusion"
    WASTE_10_03_09 = "10 03 09*", "10 03 09* - crasses noires de seconde fusion"
    WASTE_10_03_15 = (
        "10 03 15*",
        "10 03 15* - écumes inflammables ou émettant, au contact de l'eau, des gaz inflammables en quantités dangereuses",
    )
    WASTE_10_03_16 = "10 03 16", "10 03 16 - écumes autres que celles visées à la rubrique 10 03 15"
    WASTE_10_03_17 = "10 03 17*", "10 03 17* - déchets goudronnés provenant de la fabrication des anodes"
    WASTE_10_03_18 = (
        "10 03 18",
        "10 03 18 - déchets carbonés provenant de la fabrication des anodes autres que ceux visés à la rubrique 10 03 17",
    )
    WASTE_10_03_19 = (
        "10 03 19*",
        "10 03 19* - poussières de filtration des fumées contenant des substances dangereuses",
    )
    WASTE_10_03_20 = (
        "10 03 20",
        "10 03 20 - poussières de filtration des fumées autres que celles visées à la rubrique 10 03 19",
    )
    WASTE_10_03_21 = (
        "10 03 21*",
        "10 03 21* - autres fines et poussières (y compris fines de broyage de crasses) contenant des substances dangereuses",
    )
    WASTE_10_03_22 = (
        "10 03 22",
        "10 03 22 - autres fines et poussières (y compris fines de broyage de crasses) autres que celles visées à la rubrique 10 03 21",
    )
    WASTE_10_03_23 = (
        "10 03 23*",
        "10 03 23* - déchets solides provenant de l'épuration des fumées contenant des substances dangereuses",
    )
    WASTE_10_03_24 = (
        "10 03 24",
        "10 03 24 - déchets solides provenant de l'épuration des fumées autres que ceux visés à la rubrique 10 03 23",
    )
    WASTE_10_03_25 = (
        "10 03 25*",
        "10 03 25* - boues et gâteaux de filtration provenant de l'épuration des fumées contenant des substances dangereuses",
    )
    WASTE_10_03_26 = (
        "10 03 26",
        "10 03 26 - boues et gâteaux de filtration provenant de l'épuration des fumées autres que ceux visés à la rubrique 10 03 25",
    )
    WASTE_10_03_27 = (
        "10 03 27*",
        "10 03 27* - déchets provenant de l'épuration des eaux de refroidissement contenant des hydrocarbures",
    )
    WASTE_10_03_28 = (
        "10 03 28",
        "10 03 28 - déchets provenant de l'épuration des eaux de refroidissement autres que ceux visés à la rubrique 10 03 27",
    )
    WASTE_10_03_29 = (
        "10 03 29*",
        "10 03 29* - déchets provenant du traitement des scories salées et du traitement des crasses noires contenant des substances dangereuses",
    )
    WASTE_10_03_30 = (
        "10 03 30",
        "10 03 30 - déchets provenant du traitement des scories salées et du traitement des crasses noires autres que ceux visés à la rubrique 10 03 29",
    )
    WASTE_10_03_99 = "10 03 99", "10 03 99 - déchets non spécifiés ailleurs"
    WASTE_10_04_01 = "10 04 01*", "10 04 01* - scories provenant de la production primaire et secondaire"
    WASTE_10_04_02 = "10 04 02*", "10 04 02* - crasses et écumes provenant de la production primaire et secondaire"
    WASTE_10_04_03 = "10 04 03*", "10 04 03* - arséniate de calcium"
    WASTE_10_04_04 = "10 04 04*", "10 04 04* - poussières de filtration des fumées"
    WASTE_10_04_05 = "10 04 05*", "10 04 05* - autres fines et poussières"
    WASTE_10_04_06 = "10 04 06*", "10 04 06* - déchets solides provenant de l'épuration des fumées"
    WASTE_10_04_07 = "10 04 07*", "10 04 07* - boues et gâteaux de filtration provenant de l'épuration des fumées"
    WASTE_10_04_09 = (
        "10 04 09*",
        "10 04 09* - déchets provenant de l'épuration des eaux de refroidissement contenant des hydrocarbures",
    )
    WASTE_10_04_10 = (
        "10 04 10",
        "10 04 10 - déchets provenant de l'épuration des eaux de refroidissement autres que ceux visés à la rubrique 10 04 09",
    )
    WASTE_10_04_99 = "10 04 99", "10 04 99 - déchets non spécifiés ailleurs"
    WASTE_10_05_01 = "10 05 01", "10 05 01 - scories provenant de la production primaire et secondaire"
    WASTE_10_05_03 = "10 05 03*", "10 05 03* - poussières de filtration des fumées"
    WASTE_10_05_04 = "10 05 04", "10 05 04 - autres fines et poussières"
    WASTE_10_05_05 = "10 05 05*", "10 05 05* - déchets solides provenant de l'épuration des fumées"
    WASTE_10_05_06 = "10 05 06*", "10 05 06* - boues et gâteaux de filtration provenant de l'épuration des fumées"
    WASTE_10_05_08 = (
        "10 05 08*",
        "10 05 08* - déchets provenant de l'épuration des eaux de refroidissement contenant des hydrocarbures",
    )
    WASTE_10_05_09 = (
        "10 05 09",
        "10 05 09 - déchets provenant de l'épuration des eaux de refroidissement autres que ceux visés à la rubrique 10 05 08",
    )
    WASTE_10_05_10 = (
        "10 05 10*",
        "10 05 10* - crasses et écumes inflammables ou émettant, au contact de l'eau, des gaz inflammables en quantités dangereuses",
    )
    WASTE_10_05_11 = "10 05 11", "10 05 11 - crasses et écumes autres que celles visées à la rubrique 10 05 10"
    WASTE_10_05_99 = "10 05 99", "10 05 99 - déchets non spécifiés ailleurs"
    WASTE_10_06_01 = "10 06 01", "10 06 01 - scories provenant de la production primaire et secondaire"
    WASTE_10_06_02 = "10 06 02", "10 06 02 - crasses et écumes provenant de la production primaire et secondaire"
    WASTE_10_06_03 = "10 06 03*", "10 06 03* - poussières de filtration des fumées"
    WASTE_10_06_04 = "10 06 04", "10 06 04 - autres fines et poussières"
    WASTE_10_06_06 = "10 06 06*", "10 06 06* - déchets solides provenant de l'épuration des fumées"
    WASTE_10_06_07 = "10 06 07*", "10 06 07* - boues et gâteaux de filtration provenant de l'épuration des fumées"
    WASTE_10_06_09 = (
        "10 06 09*",
        "10 06 09* - déchets provenant de l'épuration des eaux de refroidissement contenant des hydrocarbures",
    )
    WASTE_10_06_10 = (
        "10 06 10",
        "10 06 10 - déchets provenant de l'épuration des eaux de refroidissement autres que ceux visés à la rubrique 10 06 09",
    )
    WASTE_10_06_99 = "10 06 99", "10 06 99 - déchets non spécifiés ailleurs"
    WASTE_10_07_01 = "10 07 01", "10 07 01 - scories provenant de la production primaire et secondaire"
    WASTE_10_07_02 = "10 07 02", "10 07 02 - crasses et écumes provenant de la production primaire et secondaire"
    WASTE_10_07_03 = "10 07 03", "10 07 03 - déchets solides provenant de l'épuration des fumées"
    WASTE_10_07_04 = "10 07 04", "10 07 04 - autres fines et poussières"
    WASTE_10_07_05 = "10 07 05", "10 07 05 - boues et gâteaux de filtration provenant de l'épuration des fumées"
    WASTE_10_07_07 = (
        "10 07 07*",
        "10 07 07* - déchets provenant de l'épuration des eaux de refroidissement contenant des hydrocarbures",
    )
    WASTE_10_07_08 = (
        "10 07 08",
        "10 07 08 - déchets provenant de l'épuration des eaux de refroidissement autres que ceux visés à la rubrique 10 07 07",
    )
    WASTE_10_07_99 = "10 07 99", "10 07 99 - déchets non spécifiés ailleurs"
    WASTE_10_08_04 = "10 08 04", "10 08 04 - fines et poussières"
    WASTE_10_08_08 = "10 08 08*", "10 08 08* - scories salées provenant de la production primaire et secondaire"
    WASTE_10_08_09 = "10 08 09", "10 08 09 - autres scories"
    WASTE_10_08_10 = (
        "10 08 10*",
        "10 08 10* - crasses et écumes inflammables ou émettant, au contact de l'eau, des gaz inflammables en quantités dangereuses",
    )
    WASTE_10_08_11 = "10 08 11", "10 08 11 - crasses et écumes autres que celles visées à la rubrique 10 08 10"
    WASTE_10_08_12 = "10 08 12*", "10 08 12* - déchets goudronnés provenant de la fabrication des anodes"
    WASTE_10_08_13 = (
        "10 08 13",
        "10 08 13 - déchets carbonés provenant de la fabrication des anodes autres que ceux visés à la rubrique 10 08 12",
    )
    WASTE_10_08_14 = "10 08 14", "10 08 14 - déchets d'anodes"
    WASTE_10_08_15 = (
        "10 08 15*",
        "10 08 15* - poussières de filtration des fumées contenant des substances dangereuses",
    )
    WASTE_10_08_16 = (
        "10 08 16",
        "10 08 16 - poussières de filtration des fumées autres que celles visées à la rubrique 10 08 15",
    )
    WASTE_10_08_17 = (
        "10 08 17*",
        "10 08 17* - boues et gâteaux de filtration provenant de l'épuration des fumées contenant des substances dangereuses",
    )
    WASTE_10_08_18 = (
        "10 08 18",
        "10 08 18 - boues et gâteaux de filtration provenant de l'épuration des fumées autres que ceux visés à la rubrique 10 08 17",
    )
    WASTE_10_08_19 = (
        "10 08 19*",
        "10 08 19* - déchets provenant de l'épuration des eaux de refroidissement contenant des hydrocarbures",
    )
    WASTE_10_08_20 = (
        "10 08 20",
        "10 08 20 - déchets provenant de l'épuration des eaux de refroidissement autres que ceux visés à la rubrique 10 08 19",
    )
    WASTE_10_08_99 = "10 08 99", "10 08 99 - déchets non spécifiés ailleurs"
    WASTE_10_09_03 = "10 09 03", "10 09 03 - laitiers de four de fonderie"
    WASTE_10_09_05 = (
        "10 09 05*",
        "10 09 05* - noyaux et moules de fonderie n'ayant pas subi la coulée contenant des substances dangereuses",
    )
    WASTE_10_09_06 = (
        "10 09 06",
        "10 09 06 - noyaux et moules de fonderie n'ayant pas subi la coulée autres que ceux visés à la rubrique 10 09 05",
    )
    WASTE_10_09_07 = (
        "10 09 07*",
        "10 09 07* - noyaux et moules de fonderie ayant subi la coulée contenant des substances dangereuses",
    )
    WASTE_10_09_08 = (
        "10 09 08",
        "10 09 08 - noyaux et moules de fonderie ayant subi la coulée autres que ceux visés à la rubrique 10 09 07",
    )
    WASTE_10_09_09 = (
        "10 09 09*",
        "10 09 09* - poussières de filtration des fumées contenant des substances dangereuses",
    )
    WASTE_10_09_10 = (
        "10 09 10",
        "10 09 10 - poussières de filtration des fumées autres que celles visées à la rubrique 10 09 09",
    )
    WASTE_10_09_11 = "10 09 11*", "10 09 11* - autres fines contenant des substances dangereuses"
    WASTE_10_09_12 = "10 09 12", "10 09 12 - autres fines non visées à la rubrique 10 09 11"
    WASTE_10_09_13 = "10 09 13*", "10 09 13* - déchets de liants contenant des substances dangereuses"
    WASTE_10_09_14 = "10 09 14", "10 09 14 - déchets de liants autres que ceux visés à la rubrique 10 09 13"
    WASTE_10_09_15 = "10 09 15*", "10 09 15* - révélateur de criques usagé contenant des substances dangereuses"
    WASTE_10_09_16 = "10 09 16", "10 09 16 - révélateur de criques usagé autre que celui visé à la rubrique 10 09 15"
    WASTE_10_09_99 = "10 09 99", "10 09 99 - déchets non spécifiés ailleurs"
    WASTE_10_10_03 = "10 10 03", "10 10 03 - laitiers de four de fonderie"
    WASTE_10_10_05 = (
        "10 10 05*",
        "10 10 05* - noyaux et moules de fonderie n'ayant pas subi la coulée contenant des substances dangereuses",
    )
    WASTE_10_10_06 = (
        "10 10 06",
        "10 10 06 - noyaux et moules de fonderie n'ayant pas subi la coulée autres que ceux visés à la rubrique 10 10 05",
    )
    WASTE_10_10_07 = (
        "10 10 07*",
        "10 10 07* - noyaux et moules de fonderie ayant subi la coulée contenant des substances dangereuses",
    )
    WASTE_10_10_08 = (
        "10 10 08",
        "10 10 08 - noyaux et moules de fonderie ayant subi la coulée autres que ceux visés à la rubrique 10 10 07",
    )
    WASTE_10_10_09 = (
        "10 10 09*",
        "10 10 09* - poussières de filtration des fumées contenant des substances dangereuses",
    )
    WASTE_10_10_10 = (
        "10 10 10",
        "10 10 10 - poussières de filtration des fumées autres que celles visées à la rubrique 10 10 09",
    )
    WASTE_10_10_11 = "10 10 11*", "10 10 11* - autres fines contenant des substances dangereuses"
    WASTE_10_10_12 = "10 10 12", "10 10 12 - autres fines non visées à la rubrique 10 10 11"
    WASTE_10_10_13 = "10 10 13*", "10 10 13* - déchets de liants contenant des substances dangereuses"
    WASTE_10_10_14 = "10 10 14", "10 10 14 - déchets de liants autres que ceux visés à la rubrique 10 10 13"
    WASTE_10_10_15 = "10 10 15*", "10 10 15* - révélateur de criques usagé contenant des substances dangereuses"
    WASTE_10_10_16 = "10 10 16", "10 10 16 - révélateur de criques usagé autre que celui visé à la rubrique 10 10 15"
    WASTE_10_10_99 = "10 10 99", "10 10 99 - déchets non spécifiés ailleurs"
    WASTE_10_11_03 = "10 11 03", "10 11 03 - déchets de matériaux à base de fibre de verre"
    WASTE_10_11_05 = "10 11 05", "10 11 05 - fines et poussières"
    WASTE_10_11_09 = (
        "10 11 09*",
        "10 11 09* - déchets de préparation avant cuisson contenant des substances dangereuses",
    )
    WASTE_10_11_10 = (
        "10 11 10",
        "10 11 10 - déchets de préparation avant cuisson autres que ceux visés à la rubrique 10 11 09",
    )
    WASTE_10_11_11 = (
        "10 11 11*",
        "10 11 11* - petites particules de déchets de verre et poudre de verre contenant des métaux lourds (par exemple tubes cathodiques)",
    )
    WASTE_10_11_12 = "10 11 12", "10 11 12 - déchets de verre autres que ceux visés à la rubrique 10 11 11"
    WASTE_10_11_13 = (
        "10 11 13*",
        "10 11 13* - boues de polissage et de meulage du verre contenant des substances dangereuses",
    )
    WASTE_10_11_14 = (
        "10 11 14",
        "10 11 14 - boues de polissage et de meulage du verre autres que celles visées à la rubrique 10 11 13",
    )
    WASTE_10_11_15 = (
        "10 11 15*",
        "10 11 15* - déchets solides provenant de l'épuration des fumées contenant des substances dangereuses",
    )
    WASTE_10_11_16 = (
        "10 11 16",
        "10 11 16 - déchets solides provenant de l'épuration des fumées autres que ceux visés à la rubrique 10 11 15",
    )
    WASTE_10_11_17 = (
        "10 11 17*",
        "10 11 17* - boues et gâteaux de filtration provenant de l'épuration des fumées contenant des substances dangereuses",
    )
    WASTE_10_11_18 = (
        "10 11 18",
        "10 11 18 - boues et gâteaux de filtration provenant de l'épuration des fumées autres que ceux visés à la rubrique 10 11 17",
    )
    WASTE_10_11_19 = (
        "10 11 19*",
        "10 11 19* - déchets solides provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_10_11_20 = (
        "10 11 20",
        "10 11 20 - déchets solides provenant du traitement in situ des effluents autres que ceux visés à la rubrique 10 11 19",
    )
    WASTE_10_11_99 = "10 11 99", "10 11 99 - déchets non spécifiés ailleurs"
    WASTE_10_12_01 = "10 12 01", "10 12 01 - déchets de préparation avant cuisson"
    WASTE_10_12_03 = "10 12 03", "10 12 03 - fines et poussières"
    WASTE_10_12_05 = "10 12 05", "10 12 05 - boues et gâteaux de filtration provenant de l'épuration des fumées"
    WASTE_10_12_06 = "10 12 06", "10 12 06 - moules déclassés"
    WASTE_10_12_08 = (
        "10 12 08",
        "10 12 08 - déchets de produits en céramique, briques, carrelage et matériaux de construction (après cuisson)",
    )
    WASTE_10_12_09 = (
        "10 12 09*",
        "10 12 09* - déchets solides provenant de l'épuration des fumées contenant des substances dangereuses",
    )
    WASTE_10_12_10 = (
        "10 12 10",
        "10 12 10 - déchets solides provenant de l'épuration des fumées autres que ceux visés à la rubrique 10 12 09",
    )
    WASTE_10_12_11 = "10 12 11*", "10 12 11* - déchets de glaçure contenant des métaux lourds"
    WASTE_10_12_12 = "10 12 12", "10 12 12 - déchets de glaçure autres que ceux visés à la rubrique 10 12 11"
    WASTE_10_12_13 = "10 12 13", "10 12 13 - boues provenant du traitement in situ des effluents"
    WASTE_10_12_99 = "10 12 99", "10 12 99 - déchets non spécifiés ailleurs"
    WASTE_10_13_01 = "10 13 01", "10 13 01 - déchets de préparation avant cuisson"
    WASTE_10_13_04 = "10 13 04", "10 13 04 - déchets de calcination et d'hydratation de la chaux"
    WASTE_10_13_06 = "10 13 06", "10 13 06 - fines et poussières (sauf rubriques 10 13 12 et 10 13 13)"
    WASTE_10_13_07 = "10 13 07", "10 13 07 - boues et gâteaux de filtration provenant de l'épuration des fumées"
    WASTE_10_13_09 = (
        "10 13 09*",
        "10 13 09* - déchets provenant de la fabrication d'amiante-ciment contenant de l'amiante",
    )
    WASTE_10_13_10 = (
        "10 13 10",
        "10 13 10 - déchets provenant de la fabrication d'amiante-ciment autres que ceux visés à la rubrique 10 13 09",
    )
    WASTE_10_13_11 = (
        "10 13 11",
        "10 13 11 - déchets provenant de la fabrication de matériaux composites à base de ciment autres que ceux visés aux rubriques 10 13 09 et 10 13 10",
    )
    WASTE_10_13_12 = (
        "10 13 12*",
        "10 13 12* - déchets solides provenant de l'épuration des fumées contenant des substances dangereuses",
    )
    WASTE_10_13_13 = (
        "10 13 13",
        "10 13 13 - déchets solides provenant de l'épuration des fumées autres que ceux visés à la rubrique 10 13 12",
    )
    WASTE_10_13_14 = "10 13 14", "10 13 14 - déchets et boues de béton"
    WASTE_10_13_99 = "10 13 99", "10 13 99 - déchets non spécifiés ailleurs"
    WASTE_10_14_01 = "10 14 01*", "10 14 01* - déchets provenant de l'épuration des fumées contenant du mercure"
    WASTE_11_01_05 = "11 01 05*", "11 01 05* - acides de décapage"
    WASTE_11_01_06 = "11 01 06*", "11 01 06* - acides non spécifiés ailleurs"
    WASTE_11_01_07 = "11 01 07*", "11 01 07* - bases de décapage"
    WASTE_11_01_08 = "11 01 08*", "11 01 08* - boues de phosphatation"
    WASTE_11_01_09 = "11 01 09*", "11 01 09* - boues et gâteaux de filtration contenant des substances dangereuses"
    WASTE_11_01_10 = (
        "11 01 10",
        "11 01 10 - boues et gâteaux de filtration autres que ceux visés à la rubrique 11 01 09",
    )
    WASTE_11_01_11 = "11 01 11*", "11 01 11* - liquides aqueux de rinçage contenant des substances dangereuses"
    WASTE_11_01_12 = "11 01 12", "11 01 12 - liquides aqueux de rinçage autres que ceux visés à la rubrique 11 01 11"
    WASTE_11_01_13 = "11 01 13*", "11 01 13* - déchets de dégraissage contenant des substances dangereuses"
    WASTE_11_01_14 = "11 01 14", "11 01 14 - déchets de dégraissage autres que ceux visés à la rubrique 11 01 13"
    WASTE_11_01_15 = (
        "11 01 15*",
        "11 01 15* - éluats et boues provenant des systèmes à membrane et des systèmes d'échange d'ions contenant des substances dangereuses",
    )
    WASTE_11_01_16 = "11 01 16*", "11 01 16* - résines échangeuses d'ions saturées ou usées"
    WASTE_11_01_98 = "11 01 98*", "11 01 98* - autres déchets contenant des substances dangereuses"
    WASTE_11_01_99 = "11 01 99", "11 01 99 - déchets non spécifiés ailleurs"
    WASTE_11_02_02 = (
        "11 02 02*",
        "11 02 02* - boues provenant de l'hydrométallurgie du zinc (y compris jarosite et goethite)",
    )
    WASTE_11_02_03 = (
        "11 02 03",
        "11 02 03 - déchets provenant de la production d'anodes pour les procédés d'électrolyse aqueuse",
    )
    WASTE_11_02_05 = (
        "11 02 05*",
        "11 02 05* - déchets provenant des procédés hydrométallurgiques du cuivre contenant des substances dangereuses",
    )
    WASTE_11_02_06 = (
        "11 02 06",
        "11 02 06 - déchets provenant des procédés hydrométallurgiques du cuivre autres que ceux visés à la rubrique 11 02 05",
    )
    WASTE_11_02_07 = "11 02 07*", "11 02 07* - autres déchets contenant des substances dangereuses"
    WASTE_11_02_99 = "11 02 99", "11 02 99 - déchets non spécifiés ailleurs"
    WASTE_11_03_01 = "11 03 01*", "11 03 01* - déchets cyanurés"
    WASTE_11_03_02 = "11 03 02*", "11 03 02* - autres déchets"
    WASTE_11_05_01 = "11 05 01", "11 05 01 - mattes"
    WASTE_11_05_02 = "11 05 02", "11 05 02 - cendres de zinc"
    WASTE_11_05_03 = "11 05 03*", "11 05 03* - déchets solides provenant de l'épuration des fumées"
    WASTE_11_05_04 = "11 05 04*", "11 05 04* - flux utilisé"
    WASTE_11_05_99 = "11 05 99", "11 05 99 - déchets non spécifiés ailleurs"
    WASTE_12_01_01 = "12 01 01", "12 01 01 - limaille et chutes de métaux ferreux"
    WASTE_12_01_02 = "12 01 02", "12 01 02 - fines et poussières de métaux ferreux"
    WASTE_12_01_03 = "12 01 03", "12 01 03 - limaille et chutes de métaux non ferreux"
    WASTE_12_01_04 = "12 01 04", "12 01 04 - fines et poussières de métaux non ferreux"
    WASTE_12_01_05 = "12 01 05", "12 01 05 - déchets de matières plastiques d'ébarbage et de tournage"
    WASTE_12_01_06 = (
        "12 01 06*",
        "12 01 06* - huiles d'usinage à base minérale contenant des halogènes (pas sous forme d'émulsions ou de solutions)",
    )
    WASTE_12_01_07 = (
        "12 01 07*",
        "12 01 07* - huiles d'usinage à base minérale sans halogènes (pas sous forme d'émulsions ou de solutions)",
    )
    WASTE_12_01_08 = "12 01 08*", "12 01 08* - émulsions et solutions d'usinage contenant des halogènes"
    WASTE_12_01_09 = "12 01 09*", "12 01 09* - émulsions et solutions d'usinage sans halogènes"
    WASTE_12_01_10 = "12 01 10*", "12 01 10* - huiles d'usinage de synthèse"
    WASTE_12_01_12 = "12 01 12*", "12 01 12* - déchets de cires et graisses"
    WASTE_12_01_13 = "12 01 13", "12 01 13 - déchets de soudure"
    WASTE_12_01_14 = "12 01 14*", "12 01 14* - boues d'usinage contenant des substances dangereuses"
    WASTE_12_01_15 = "12 01 15", "12 01 15 - boues d'usinage autres que celles visées à la rubrique 12 01 14"
    WASTE_12_01_16 = "12 01 16*", "12 01 16* - déchets de grenaillage contenant des substances dangereuses"
    WASTE_12_01_17 = "12 01 17", "12 01 17 - déchets de grenaillage autres que ceux visés à la rubrique 12 01 16"
    WASTE_12_01_18 = (
        "12 01 18*",
        "12 01 18* - boues métalliques (provenant du meulage et de l'affûtage) contenant des hydrocarbures",
    )
    WASTE_12_01_19 = "12 01 19*", "12 01 19* - huiles d'usinage facilement biodégradables"
    WASTE_12_01_20 = (
        "12 01 20*",
        "12 01 20* - déchets de meulage et matériaux de meulage contenant des substances dangereuses",
    )
    WASTE_12_01_21 = (
        "12 01 21",
        "12 01 21 - déchets de meulage et matériaux de meulage autres que ceux visés à la rubrique 12 01 20",
    )
    WASTE_12_01_99 = "12 01 99", "12 01 99 - déchets non spécifiés ailleurs"
    WASTE_12_03_01 = "12 03 01*", "12 03 01* - liquides aqueux de nettoyage"
    WASTE_12_03_02 = "12 03 02*", "12 03 02* - déchets du dégraissage à la vapeur"
    WASTE_13_01_01 = "13 01 01*", "13 01 01* - huiles hydrauliques contenant des PCB"
    WASTE_13_01_04 = "13 01 04*", "13 01 04* - huiles hydrauliques chlorées (émulsions)"
    WASTE_13_01_05 = "13 01 05*", "13 01 05* - huiles hydrauliques non chlorées (émulsions)"
    WASTE_13_01_09 = "13 01 09*", "13 01 09* - huiles hydrauliques chlorées à base minérale"
    WASTE_13_01_10 = "13 01 10*", "13 01 10* - huiles hydrauliques non chlorées à base minérale"
    WASTE_13_01_11 = "13 01 11*", "13 01 11* - huiles hydrauliques synthétiques"
    WASTE_13_01_12 = "13 01 12*", "13 01 12* - huiles hydrauliques facilement biodégradables"
    WASTE_13_01_13 = "13 01 13*", "13 01 13* - autres huiles hydrauliques"
    WASTE_13_02_04 = (
        "13 02 04*",
        "13 02 04* - huiles moteur, de boîte de vitesses et de lubrification chlorées à base minérale",
    )
    WASTE_13_02_05 = (
        "13 02 05*",
        "13 02 05* - huiles moteur, de boîte de vitesses et de lubrification non chlorées à base minérale",
    )
    WASTE_13_02_06 = "13 02 06*", "13 02 06* - huiles moteur, de boîte de vitesses et de lubrification synthétiques"
    WASTE_13_02_07 = (
        "13 02 07*",
        "13 02 07* - huiles moteur, de boîte de vitesses et de lubrification facilement biodégradables",
    )
    WASTE_13_02_08 = "13 02 08*", "13 02 08* - autres huiles moteur, de boîte de vitesses et de lubrification"
    WASTE_13_03_01 = "13 03 01*", "13 03 01* - huiles isolantes et fluides caloporteurs contenant des PCB"
    WASTE_13_03_06 = (
        "13 03 06*",
        "13 03 06* - huiles isolantes et fluides caloporteurs chlorés à base minérale autres que ceux visés à la rubrique 13 03 01",
    )
    WASTE_13_03_07 = "13 03 07*", "13 03 07* - huiles isolantes et fluides caloporteurs non chlorés à base minérale"
    WASTE_13_03_08 = "13 03 08*", "13 03 08* - huiles isolantes et fluides caloporteurs synthétiques"
    WASTE_13_03_09 = "13 03 09*", "13 03 09* - huiles isolantes et fluides caloporteurs facilement biodégradables"
    WASTE_13_03_10 = "13 03 10*", "13 03 10* - autres huiles isolantes et fluides caloporteurs"
    WASTE_13_04_01 = "13 04 01*", "13 04 01* - hydrocarbures de fond de cale provenant de la navigation fluviale"
    WASTE_13_04_02 = "13 04 02*", "13 04 02* - hydrocarbures de fond de cale provenant de canalisations de môles"
    WASTE_13_04_03 = "13 04 03*", "13 04 03* - hydrocarbures de fond de cale provenant d'un autre type de navigation"
    WASTE_13_05_01 = (
        "13 05 01*",
        "13 05 01* - déchets solides provenant de dessableurs et de séparateurs eau/hydrocarbures",
    )
    WASTE_13_05_02 = "13 05 02*", "13 05 02* - boues provenant de séparateurs eau/hydrocarbures"
    WASTE_13_05_03 = "13 05 03*", "13 05 03* - boues provenant de déshuileurs"
    WASTE_13_05_06 = "13 05 06*", "13 05 06* - hydrocarbures provenant de séparateurs eau/hydrocarbures"
    WASTE_13_05_07 = (
        "13 05 07*",
        "13 05 07* - eau mélangée à des hydrocarbures provenant de séparateurs eau/hydrocarbures",
    )
    WASTE_13_05_08 = (
        "13 05 08*",
        "13 05 08* - mélanges de déchets provenant de dessableurs et de séparateurs eau/hydrocarbures",
    )
    WASTE_13_07_01 = "13 07 01*", "13 07 01* - fuel oil et diesel"
    WASTE_13_07_02 = "13 07 02*", "13 07 02* - essence"
    WASTE_13_07_03 = "13 07 03*", "13 07 03* - autres combustibles (y compris mélanges)"
    WASTE_13_08_01 = "13 08 01*", "13 08 01* - boues ou émulsions de dessalage"
    WASTE_13_08_02 = "13 08 02*", "13 08 02* - autres émulsions"
    WASTE_13_08_99 = "13 08 99*", "13 08 99* - déchets non spécifiés ailleurs"
    WASTE_14_06_01 = "14 06 01*", "14 06 01* - chlorofluorocarbones, HCFC, HFC"
    WASTE_14_06_02 = "14 06 02*", "14 06 02* - autres solvants et mélanges de solvants halogénés"
    WASTE_14_06_03 = "14 06 03*", "14 06 03* - autres solvants et mélanges de solvants"
    WASTE_14_06_04 = "14 06 04*", "14 06 04* - boues ou déchets solides contenant des solvants halogénés"
    WASTE_14_06_05 = "14 06 05*", "14 06 05* - boues ou déchets solides contenant d'autres solvants"
    WASTE_15_01_01 = "15 01 01", "15 01 01 - emballages en papier/carton"
    WASTE_15_01_02 = "15 01 02", "15 01 02 - emballages en matières plastiques"
    WASTE_15_01_03 = "15 01 03", "15 01 03 - emballages en bois"
    WASTE_15_01_04 = "15 01 04", "15 01 04 - emballages métalliques"
    WASTE_15_01_05 = "15 01 05", "15 01 05 - emballages composites"
    WASTE_15_01_06 = "15 01 06", "15 01 06 - emballages en mélange"
    WASTE_15_01_07 = "15 01 07", "15 01 07 - emballages en verre"
    WASTE_15_01_09 = "15 01 09", "15 01 09 - emballages textiles"
    WASTE_15_01_10 = (
        "15 01 10*",
        "15 01 10* - emballages contenant des résidus de substances dangereuses ou contaminés par de tels résidus",
    )
    WASTE_15_01_11 = (
        "15 01 11*",
        "15 01 11* - emballages métalliques contenant une matrice poreuse solide dangereuse (par exemple amiante), y compris des conteneurs à pression vides",
    )
    WASTE_15_02_02 = (
        "15 02 02*",
        "15 02 02* - absorbants, matériaux filtrants (y compris les filtres à huile non spécifiés ailleurs), chiffons d'essuyage et vêtements de protection contaminés par des substances dangereuses",
    )
    WASTE_15_02_03 = (
        "15 02 03",
        "15 02 03 - absorbants, matériaux filtrants, chiffons d'essuyage et vêtements de protection autres que ceux visés à la rubrique 15 02 02",
    )
    WASTE_16_01_03 = "16 01 03", "16 01 03 - pneus hors d'usage"
    WASTE_16_01_04 = "16 01 04*", "16 01 04* - véhicules hors d'usage"
    WASTE_16_01_06 = (
        "16 01 06",
        "16 01 06 - véhicules hors d'usage ne contenant ni liquides ni autres composants dangereux",
    )
    WASTE_16_01_07 = "16 01 07*", "16 01 07* - filtres à huile"
    WASTE_16_01_08 = "16 01 08*", "16 01 08* - composants contenant du mercure"
    WASTE_16_01_09 = "16 01 09*", "16 01 09* - composants contenant des PCB"
    WASTE_16_01_10 = "16 01 10*", "16 01 10* - composants explosifs (par exemple coussins gonflables de sécurité)"
    WASTE_16_01_11 = "16 01 11*", "16 01 11* - patins de freins contenant de l'amiante"
    WASTE_16_01_12 = "16 01 12", "16 01 12 - patins de freins autres que ceux visés à la rubrique 16 01 11"
    WASTE_16_01_13 = "16 01 13*", "16 01 13* - liquides de frein"
    WASTE_16_01_14 = "16 01 14*", "16 01 14* - antigels contenant des substances dangereuses"
    WASTE_16_01_15 = "16 01 15", "16 01 15 - antigels autres que ceux visés à la rubrique 16 01 14"
    WASTE_16_01_16 = "16 01 16", "16 01 16 - réservoirs de gaz liquéfié"
    WASTE_16_01_17 = "16 01 17", "16 01 17 - métaux ferreux"
    WASTE_16_01_18 = "16 01 18", "16 01 18 - métaux non ferreux"
    WASTE_16_01_19 = "16 01 19", "16 01 19 - matières plastiques"
    WASTE_16_01_20 = "16 01 20", "16 01 20 - verre"
    WASTE_16_01_21 = (
        "16 01 21*",
        "16 01 21* - composants dangereux autres que ceux visés aux rubriques 16 01 07 à 16 01 11, 16 01 13 et 16 01 14",
    )
    WASTE_16_01_22 = "16 01 22", "16 01 22 - composants non spécifiés ailleurs"
    WASTE_16_01_99 = "16 01 99", "16 01 99 - déchets non spécifiés ailleurs"
    WASTE_16_02_09 = "16 02 09*", "16 02 09* - transformateurs et accumulateurs contenant des PCB"
    WASTE_16_02_10 = (
        "16 02 10*",
        "16 02 10* - équipements mis au rebut contenant des PCB ou contaminés par de telles substances autres que ceux visés à la rubrique 16 02 09",
    )
    WASTE_16_02_11 = (
        "16 02 11*",
        "16 02 11* - équipements mis au rebut contenant des chlorofluorocarbones, des HCFC ou des HFC",
    )
    WASTE_16_02_12 = "16 02 12*", "16 02 12* - équipements mis au rebut contenant de l'amiante libre"
    WASTE_16_02_13 = (
        "16 02 13*",
        "16 02 13* - équipements mis au rebut contenant des composants dangereux (3) autres que ceux visés aux rubriques 16 02 09 à 16 02 12",
    )
    WASTE_16_02_14 = (
        "16 02 14",
        "16 02 14 - équipements mis au rebut autres que ceux visés aux rubriques 16 02 09 à 16 02 13",
    )
    WASTE_16_02_15 = "16 02 15*", "16 02 15* - composants dangereux retirés des équipements mis au rebut"
    WASTE_16_02_16 = (
        "16 02 16",
        "16 02 16 - composants retirés des équipements mis au rebut autres que ceux visés à la rubrique 16 02 15",
    )
    WASTE_16_03_03 = "16 03 03*", "16 03 03* - déchets d'origine minérale contenant des substances dangereuses"
    WASTE_16_03_04 = "16 03 04", "16 03 04 - déchets d'origine minérale autres que ceux visés à la rubrique 16 03 03"
    WASTE_16_03_05 = "16 03 05*", "16 03 05* - déchets d'origine organique contenant des substances dangereuses"
    WASTE_16_03_06 = "16 03 06", "16 03 06 - déchets d'origine organique autres que ceux visés à la rubrique 16 03 05"
    WASTE_16_03_07 = "16 03 07*", "16 03 07* - mercure métallique"
    WASTE_16_04_01 = "16 04 01*", "16 04 01* - déchets de munitions"
    WASTE_16_04_02 = "16 04 02*", "16 04 02* - déchets de feux d'artifice"
    WASTE_16_04_03 = "16 04 03*", "16 04 03* - autres déchets d'explosifs"
    WASTE_16_05_04 = (
        "16 05 04*",
        "16 05 04* - gaz en récipients à pression (y compris les halons) contenant des substances dangereuses",
    )
    WASTE_16_05_05 = "16 05 05", "16 05 05 - gaz en récipients à pression autres que ceux visés à la rubrique 16 05 04"
    WASTE_16_05_06 = (
        "16 05 06*",
        "16 05 06* - produits chimiques de laboratoire à base de ou contenant des substances dangereuses, y compris les mélanges de produits chimiques de laboratoire",
    )
    WASTE_16_05_07 = (
        "16 05 07*",
        "16 05 07* - produits chimiques d'origine minérale à base de ou contenant des substances dangereuses, mis au rebut",
    )
    WASTE_16_05_08 = (
        "16 05 08*",
        "16 05 08* - produits chimiques d'origine organique à base de ou contenant des substances dangereuses, mis au rebut",
    )
    WASTE_16_05_09 = (
        "16 05 09",
        "16 05 09 - produits chimiques mis au rebut autres que ceux visés aux rubriques 16 05 06, 16 05 07 ou 16 05 08",
    )
    WASTE_16_06_01 = "16 06 01*", "16 06 01* - accumulateurs au plomb"
    WASTE_16_06_02 = "16 06 02*", "16 06 02* - accumulateurs Ni-Cd"
    WASTE_16_06_03 = "16 06 03*", "16 06 03* - piles contenant du mercure"
    WASTE_16_06_04 = "16 06 04", "16 06 04 - piles alcalines (sauf rubrique 16 06 03)"
    WASTE_16_06_05 = "16 06 05", "16 06 05 - autres piles et accumulateurs"
    WASTE_16_06_06 = "16 06 06*", "16 06 06* - électrolytes de piles et accumulateurs collectés séparément"
    WASTE_16_07_08 = "16 07 08*", "16 07 08* - déchets contenant des hydrocarbures"
    WASTE_16_07_09 = "16 07 09*", "16 07 09* - déchets contenant d'autres substances dangereuses"
    WASTE_16_07_99 = "16 07 99", "16 07 99 - déchets non spécifiés ailleurs"
    WASTE_16_08_01 = (
        "16 08 01",
        "16 08 01 - catalyseurs usés contenant de l'or, de l'argent, du rhénium, du rhodium, du palladium, de l'iridium ou du platine (sauf rubrique 16 08 07)",
    )
    WASTE_16_08_02 = (
        "16 08 02*",
        "16 08 02* - catalyseurs usés contenant des métaux ou composés de métaux de transition dangereux",
    )
    WASTE_16_08_03 = (
        "16 08 03",
        "16 08 03 - catalyseurs usés contenant des métaux ou composés de métaux de transition non spécifiés ailleurs",
    )
    WASTE_16_08_04 = (
        "16 08 04",
        "16 08 04 - catalyseurs usés de craquage catalytique sur lit fluide (sauf rubrique 16 08 07)",
    )
    WASTE_16_08_05 = "16 08 05*", "16 08 05* - catalyseurs usés contenant de l'acide phosphorique"
    WASTE_16_08_06 = "16 08 06*", "16 08 06* - liquides usés employés comme catalyseurs"
    WASTE_16_08_07 = "16 08 07*", "16 08 07* - catalyseurs usés contaminés par des substances dangereuses"
    WASTE_16_09_01 = "16 09 01*", "16 09 01* - permanganates, par exemple, permanganate de potassium"
    WASTE_16_09_02 = (
        "16 09 02*",
        "16 09 02* - chromates, par exemple, chromate de potassium, dichromate de sodium ou de potassium",
    )
    WASTE_16_09_03 = "16 09 03*", "16 09 03* - peroxydes, par exemple, peroxyde d'hydrogène"
    WASTE_16_09_04 = "16 09 04*", "16 09 04* - substances oxydantes non spécifiées ailleurs"
    WASTE_16_10_01 = "16 10 01*", "16 10 01* - déchets liquides aqueux contenant des substances dangereuses"
    WASTE_16_10_02 = "16 10 02", "16 10 02 - déchets liquides aqueux autres que ceux visés à la rubrique 16 10 01"
    WASTE_16_10_03 = "16 10 03*", "16 10 03* - concentrés aqueux contenant des substances dangereuses"
    WASTE_16_10_04 = "16 10 04", "16 10 04 - concentrés aqueux autres que ceux visés à la rubrique 16 10 03"
    WASTE_16_11_01 = (
        "16 11 01*",
        "16 11 01* - revêtements de fours et réfractaires à base de carbone provenant de procédés métallurgiques contenant des substances dangereuses",
    )
    WASTE_16_11_02 = (
        "16 11 02",
        "16 11 02 - revêtements de fours et réfractaires à base de carbone provenant de procédés métallurgiques autres que ceux visés à la rubrique 16 11 01",
    )
    WASTE_16_11_03 = (
        "16 11 03*",
        "16 11 03* - autres revêtements de fours et réfractaires provenant de procédés métallurgiques contenant des substances dangereuses",
    )
    WASTE_16_11_04 = (
        "16 11 04",
        "16 11 04 - autres revêtements de fours et réfractaires provenant de procédés métallurgiques non visés à la rubrique 16 11 03",
    )
    WASTE_16_11_05 = (
        "16 11 05*",
        "16 11 05* - revêtements de fours et réfractaires provenant de procédés non métallurgiques contenant des substances dangereuses",
    )
    WASTE_16_11_06 = (
        "16 11 06",
        "16 11 06 - revêtements de fours et réfractaires provenant de procédés non métallurgiques autres que ceux visés à la rubrique 16 11 05",
    )
    WASTE_17_01_01 = "17 01 01", "17 01 01 - béton"
    WASTE_17_01_02 = "17 01 02", "17 01 02 - briques"
    WASTE_17_01_03 = "17 01 03", "17 01 03 - tuiles et céramiques"
    WASTE_17_01_06 = (
        "17 01 06*",
        "17 01 06* - mélanges ou fractions séparées de béton, briques, tuiles et céramiques contenant des substances dangereuses",
    )
    WASTE_17_01_07 = (
        "17 01 07",
        "17 01 07 - mélanges de béton, briques, tuiles et céramiques autres que ceux visés à la rubrique 17 01 06",
    )
    WASTE_17_02_01 = "17 02 01", "17 02 01 - bois"
    WASTE_17_02_02 = "17 02 02", "17 02 02 - verre"
    WASTE_17_02_03 = "17 02 03", "17 02 03 - matières plastiques"
    WASTE_17_02_04 = (
        "17 02 04*",
        "17 02 04* - bois, verre et matières plastiques contenant des substances dangereuses ou contaminés par de telles substances",
    )
    WASTE_17_03_01 = "17 03 01*", "17 03 01* - mélanges bitumineux contenant du goudron"
    WASTE_17_03_02 = "17 03 02", "17 03 02 - mélanges bitumineux autres que ceux visés à la rubrique 17 03 01"
    WASTE_17_03_03 = "17 03 03*", "17 03 03* - goudron et produits goudronnés"
    WASTE_17_04_01 = "17 04 01", "17 04 01 - cuivre, bronze, laiton"
    WASTE_17_04_02 = "17 04 02", "17 04 02 - aluminium"
    WASTE_17_04_03 = "17 04 03", "17 04 03 - plomb"
    WASTE_17_04_04 = "17 04 04", "17 04 04 - zinc"
    WASTE_17_04_05 = "17 04 05", "17 04 05 - fer et acier"
    WASTE_17_04_06 = "17 04 06", "17 04 06 - étain"
    WASTE_17_04_07 = "17 04 07", "17 04 07 - métaux en mélange"
    WASTE_17_04_09 = "17 04 09*", "17 04 09* - déchets métalliques contaminés par des substances dangereuses"
    WASTE_17_04_10 = (
        "17 04 10*",
        "17 04 10* - câbles contenant des hydrocarbures, du goudron ou d'autres substances dangereuses",
    )
    WASTE_17_04_11 = "17 04 11", "17 04 11 - câbles autres que ceux visés à la rubrique 17 04 10"
    WASTE_17_05_03 = "17 05 03*", "17 05 03* - terres et cailloux contenant des substances dangereuses"
    WASTE_17_05_04 = "17 05 04", "17 05 04 - terres et cailloux autres que ceux visés à la rubrique 17 05 03"
    WASTE_17_05_05 = "17 05 05*", "17 05 05* - boues de dragage contenant des substances dangereuses"
    WASTE_17_05_06 = "17 05 06", "17 05 06 - boues de dragage autres que celles visées à la rubrique 17 05 05"
    WASTE_17_05_07 = "17 05 07*", "17 05 07* - ballast de voie contenant des substances dangereuses"
    WASTE_17_05_08 = "17 05 08", "17 05 08 - ballast de voie autre que celui visé à la rubrique 17 05 07"
    WASTE_17_06_01 = "17 06 01*", "17 06 01* - matériaux d'isolation contenant de l'amiante"
    WASTE_17_06_03 = (
        "17 06 03*",
        "17 06 03* - autres matériaux d'isolation à base de ou contenant des substances dangereuses",
    )
    WASTE_17_06_04 = (
        "17 06 04",
        "17 06 04 - matériaux d'isolation autres que ceux visés aux rubriques 17 06 01 et 17 06 03",
    )
    WASTE_17_06_05 = "17 06 05*", "17 06 05* - matériaux de construction contenant de l'amiante"
    WASTE_17_08_01 = (
        "17 08 01*",
        "17 08 01* - matériaux de construction à base de gypse contaminés par des substances dangereuses",
    )
    WASTE_17_08_02 = (
        "17 08 02",
        "17 08 02 - matériaux de construction à base de gypse autres que ceux visés à la rubrique 17 08 01",
    )
    WASTE_17_09_01 = "17 09 01*", "17 09 01* - déchets de construction et de démolition contenant du mercure"
    WASTE_17_09_02 = (
        "17 09 02*",
        "17 09 02* - déchets de construction et de démolition contenant des PCB (par exemple, mastics, sols à base de résines, double vitrage, condensateurs, contenant des PCB)",
    )
    WASTE_17_09_03 = (
        "17 09 03*",
        "17 09 03* - autres déchets de construction et de démolition (y compris en mélange) contenant des substances dangereuses",
    )
    WASTE_17_09_04 = (
        "17 09 04",
        "17 09 04 - déchets de construction et de démolition en mélange autres que ceux visés aux rubriques 17 09 01, 17 09 02 et 17 09 03",
    )
    WASTE_18_01_01 = "18 01 01", "18 01 01 - objets piquants et coupants (sauf rubrique 18 01 03)"
    WASTE_18_01_02 = (
        "18 01 02",
        "18 01 02 - déchets anatomiques et organes, y compris sacs de sang et réserves de sang (sauf rubrique 18 01 03)",
    )
    WASTE_18_01_03 = (
        "18 01 03*",
        "18 01 03* - déchets dont la collecte et l'élimination font l'objet de prescriptions particulières vis-à-vis des risques d'infection",
    )
    WASTE_18_01_04 = (
        "18 01 04",
        "18 01 04 - déchets dont la collecte et l'élimination ne font pas l'objet de prescriptions particulières vis-à-vis des risques d'infection (par exemple vêtements, plâtres, draps, vêtements jetables, langes)",
    )
    WASTE_18_01_06 = "18 01 06*", "18 01 06* - produits chimiques à base de ou contenant des substances dangereuses"
    WASTE_18_01_07 = "18 01 07", "18 01 07 - produits chimiques autres que ceux visés à la rubrique 18 01 06"
    WASTE_18_01_08 = "18 01 08*", "18 01 08* - médicaments cytotoxiques et cytostatiques"
    WASTE_18_01_09 = "18 01 09", "18 01 09 - médicaments autres que ceux visés à la rubrique 18 01 08"
    WASTE_18_01_10 = "18 01 10*", "18 01 10* - déchets d'amalgame dentaire"
    WASTE_18_02_01 = "18 02 01", "18 02 01 - objets piquants et coupants (sauf rubrique 18 02 02)"
    WASTE_18_02_02 = (
        "18 02 02*",
        "18 02 02* - déchets dont la collecte et l'élimination font l'objet de prescriptions particulières vis-à-vis des risques d'infection",
    )
    WASTE_18_02_03 = (
        "18 02 03",
        "18 02 03 - déchets dont la collecte et l'élimination ne font pas l'objet de prescriptions particulières vis-à-vis des risques d'infection",
    )
    WASTE_18_02_05 = "18 02 05*", "18 02 05* - produits chimiques à base de ou contenant des substances dangereuses"
    WASTE_18_02_06 = "18 02 06", "18 02 06 - produits chimiques autres que ceux visés à la rubrique 18 02 05"
    WASTE_18_02_07 = "18 02 07*", "18 02 07* - médicaments cytotoxiques et cytostatiques"
    WASTE_18_02_08 = "18 02 08", "18 02 08 - médicaments autres que ceux visés à la rubrique 18 02 07"
    WASTE_19_01_02 = "19 01 02", "19 01 02 - déchets de déferraillage des mâchefers"
    WASTE_19_01_05 = "19 01 05*", "19 01 05* - gâteaux de filtration provenant de l'épuration des fumées"
    WASTE_19_01_06 = (
        "19 01 06*",
        "19 01 06* - déchets liquides aqueux provenant de l'épuration des fumées et autres déchets liquides aqueux",
    )
    WASTE_19_01_07 = "19 01 07*", "19 01 07* - déchets solides provenant de l'épuration des fumées"
    WASTE_19_01_10 = "19 01 10*", "19 01 10* - charbon actif usé provenant de l'épuration des gaz de fumées"
    WASTE_19_01_11 = "19 01 11*", "19 01 11* - mâchefers contenant des substances dangereuses"
    WASTE_19_01_12 = "19 01 12", "19 01 12 - mâchefers autres que ceux visés à la rubrique 19 01 11"
    WASTE_19_01_13 = "19 01 13*", "19 01 13* - cendres volantes contenant des substances dangereuses"
    WASTE_19_01_14 = "19 01 14", "19 01 14 - cendres volantes autres que celles visées à la rubrique 19 01 13"
    WASTE_19_01_15 = "19 01 15*", "19 01 15* - cendres sous chaudière contenant des substances dangereuses"
    WASTE_19_01_16 = "19 01 16", "19 01 16 - cendres sous chaudière autres que celles visées à la rubrique 19 01 15"
    WASTE_19_01_17 = "19 01 17*", "19 01 17* - déchets de pyrolyse contenant des substances dangereuses"
    WASTE_19_01_18 = "19 01 18", "19 01 18 - déchets de pyrolyse autres que ceux visés à la rubrique 19 01 17"
    WASTE_19_01_19 = "19 01 19", "19 01 19 - sables provenant de lits fluidisés"
    WASTE_19_01_99 = "19 01 99", "19 01 99 - déchets non spécifiés ailleurs"
    WASTE_19_02_03 = "19 02 03", "19 02 03 - déchets prémélangés composés seulement de déchets non dangereux"
    WASTE_19_02_04 = "19 02 04*", "19 02 04* - déchets prémélangés contenant au moins un déchet dangereux"
    WASTE_19_02_05 = (
        "19 02 05*",
        "19 02 05* - boues provenant des traitements physico-chimiques contenant des substances dangereuses",
    )
    WASTE_19_02_06 = (
        "19 02 06",
        "19 02 06 - boues provenant des traitements physico-chimiques autres que celles visées à la rubrique 19 02 05",
    )
    WASTE_19_02_07 = "19 02 07*", "19 02 07* - hydrocarbures et concentrés provenant d'une séparation"
    WASTE_19_02_08 = "19 02 08*", "19 02 08* - déchets combustibles liquides contenant des substances dangereuses"
    WASTE_19_02_09 = "19 02 09*", "19 02 09* - déchets combustibles solides contenant des substances dangereuses"
    WASTE_19_02_10 = (
        "19 02 10",
        "19 02 10 - déchets combustibles autres que ceux visés aux rubriques 19 02 08 et 19 02 09",
    )
    WASTE_19_02_11 = "19 02 11*", "19 02 11* - autres déchets contenant des substances dangereuses"
    WASTE_19_02_99 = "19 02 99", "19 02 99 - déchets non spécifiés ailleurs"
    WASTE_19_03_04 = (
        "19 03 04*",
        "19 03 04* - déchets marqués comme dangereux partiellement stabilisés, autres que ceux visés à la rubrique 19 03 08",
    )
    WASTE_19_03_05 = "19 03 05", "19 03 05 - déchets stabilisés autres que ceux visés à la rubrique 19 03 04"
    WASTE_19_03_06 = "19 03 06*", "19 03 06* - déchets catalogués comme dangereux, solidifiés"
    WASTE_19_03_07 = "19 03 07", "19 03 07 - déchets solidifiés autres que ceux visés à la rubrique 19 03 06"
    WASTE_19_03_08 = "19 03 08*", "19 03 08* - mercure partiellement stabilisé"
    WASTE_19_04_01 = "19 04 01", "19 04 01 - déchets vitrifiés"
    WASTE_19_04_02 = "19 04 02*", "19 04 02* - cendres volantes et autres déchets du traitement des gaz de fumée"
    WASTE_19_04_03 = "19 04 03*", "19 04 03* - phase solide non vitrifiée"
    WASTE_19_04_04 = "19 04 04", "19 04 04 - déchets liquides aqueux provenant de la trempe des déchets vitrifiés"
    WASTE_19_05_01 = "19 05 01", "19 05 01 - fraction non compostée des déchets municipaux et assimilés"
    WASTE_19_05_02 = "19 05 02", "19 05 02 - fraction non compostée des déchets animaux et végétaux"
    WASTE_19_05_03 = "19 05 03", "19 05 03 - compost déclassé"
    WASTE_19_05_99 = "19 05 99", "19 05 99 - déchets non spécifiés ailleurs"
    WASTE_19_06_03 = "19 06 03", "19 06 03 - liqueurs provenant du traitement anaérobie des déchets municipaux"
    WASTE_19_06_04 = "19 06 04", "19 06 04 - digestats provenant du traitement anaérobie des déchets municipaux"
    WASTE_19_06_05 = (
        "19 06 05",
        "19 06 05 - liqueurs provenant du traitement anaérobie des déchets animaux et végétaux",
    )
    WASTE_19_06_06 = (
        "19 06 06",
        "19 06 06 - digestats provenant du traitement anaérobie des déchets animaux et végétaux",
    )
    WASTE_19_06_99 = "19 06 99", "19 06 99 - déchets non spécifiés ailleurs"
    WASTE_19_07_02 = "19 07 02*", "19 07 02* - lixiviats de décharges contenant des substances dangereuses"
    WASTE_19_07_03 = "19 07 03", "19 07 03 - lixiviats de décharges autres que ceux visés à la rubrique 19 07 02"
    WASTE_19_08_01 = "19 08 01", "19 08 01 - déchets de dégrillage"
    WASTE_19_08_02 = "19 08 02", "19 08 02 - déchets de dessablage"
    WASTE_19_08_05 = "19 08 05", "19 08 05 - boues provenant du traitement des eaux usées urbaines"
    WASTE_19_08_06 = "19 08 06*", "19 08 06* - résines échangeuses d'ions saturées ou usées"
    WASTE_19_08_07 = "19 08 07*", "19 08 07* - solutions et boues provenant de la régénération des échangeurs d'ions"
    WASTE_19_08_08 = "19 08 08*", "19 08 08* - déchets provenant des systèmes à membrane contenant des métaux lourds"
    WASTE_19_08_09 = (
        "19 08 09",
        "19 08 09 - mélanges de graisse et d'huile provenant de la séparation huile/eaux usées contenant seulement des huiles et graisses alimentaires",
    )
    WASTE_19_08_10 = (
        "19 08 10*",
        "19 08 10* - mélanges de graisse et d'huile provenant de la séparation huile/eaux usées autres que ceux visés à la rubrique 19 08 09",
    )
    WASTE_19_08_11 = (
        "19 08 11*",
        "19 08 11* - boues contenant des substances dangereuses provenant du traitement biologique des eaux usées industrielles",
    )
    WASTE_19_08_12 = (
        "19 08 12",
        "19 08 12 - boues provenant du traitement biologique des eaux usées industrielles autres que celles visées à la rubrique 19 08 11",
    )
    WASTE_19_08_13 = (
        "19 08 13*",
        "19 08 13* - boues contenant des substances dangereuses provenant d'autres traitements des eaux usées industrielles",
    )
    WASTE_19_08_14 = (
        "19 08 14",
        "19 08 14 - boues provenant d'autres traitements des eaux usées industrielles autres que celles visées à la rubrique 19 08 13",
    )
    WASTE_19_08_99 = "19 08 99", "19 08 99 - déchets non spécifiés ailleurs"
    WASTE_19_09_01 = "19 09 01", "19 09 01 - déchets solides de première filtration et de dégrillage"
    WASTE_19_09_02 = "19 09 02", "19 09 02 - boues de clarification de l'eau"
    WASTE_19_09_03 = "19 09 03", "19 09 03 - boues de décarbonatation"
    WASTE_19_09_04 = "19 09 04", "19 09 04 - charbon actif usé"
    WASTE_19_09_05 = "19 09 05", "19 09 05 - résines échangeuses d'ions saturées ou usées"
    WASTE_19_09_06 = "19 09 06", "19 09 06 - solutions et boues provenant de la régénération des échangeurs d'ions"
    WASTE_19_09_99 = "19 09 99", "19 09 99 - déchets non spécifiés ailleurs"
    WASTE_19_10_01 = "19 10 01", "19 10 01 - déchets de fer ou d'acier"
    WASTE_19_10_02 = "19 10 02", "19 10 02 - déchets de métaux non ferreux"
    WASTE_19_10_03 = (
        "19 10 03*",
        "19 10 03* - fraction légère des résidus de broyage et poussières contenant des substances dangereuses",
    )
    WASTE_19_10_04 = (
        "19 10 04",
        "19 10 04 - fraction légère des résidus de broyage et poussières autres que celles visées à la rubrique 19 10 03",
    )
    WASTE_19_10_05 = "19 10 05*", "19 10 05* - autres fractions contenant des substances dangereuses"
    WASTE_19_10_06 = "19 10 06", "19 10 06 - autres fractions autres que celles visées à la rubrique 19 10 05"
    WASTE_19_11_01 = "19 11 01*", "19 11 01* - argiles de filtration usées"
    WASTE_19_11_02 = "19 11 02*", "19 11 02* - goudrons acides"
    WASTE_19_11_03 = "19 11 03*", "19 11 03* - déchets liquides aqueux"
    WASTE_19_11_04 = "19 11 04*", "19 11 04* - déchets provenant du nettoyage d'hydrocarbures avec des bases"
    WASTE_19_11_05 = (
        "19 11 05*",
        "19 11 05* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_19_11_06 = (
        "19 11 06",
        "19 11 06 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 19 11 05",
    )
    WASTE_19_11_07 = "19 11 07*", "19 11 07* - déchets provenant de l'épuration des gaz de combustion"
    WASTE_19_11_99 = "19 11 99", "19 11 99 - déchets non spécifiés ailleurs"
    WASTE_19_12_01 = "19 12 01", "19 12 01 - papier et carton"
    WASTE_19_12_02 = "19 12 02", "19 12 02 - métaux ferreux"
    WASTE_19_12_03 = "19 12 03", "19 12 03 - métaux non ferreux"
    WASTE_19_12_04 = "19 12 04", "19 12 04 - matières plastiques et caoutchouc"
    WASTE_19_12_05 = "19 12 05", "19 12 05 - verre"
    WASTE_19_12_06 = "19 12 06*", "19 12 06* - bois contenant des substances dangereuses"
    WASTE_19_12_07 = "19 12 07", "19 12 07 - bois autres que ceux visés à la rubrique 19 12 06"
    WASTE_19_12_08 = "19 12 08", "19 12 08 - textiles"
    WASTE_19_12_09 = "19 12 09", "19 12 09 - minéraux (par exemple sable, cailloux)"
    WASTE_19_12_10 = "19 12 10", "19 12 10 - déchets combustibles (combustible issu de déchets)"
    WASTE_19_12_11 = (
        "19 12 11*",
        "19 12 11* - autres déchets (y compris mélanges) provenant du traitement mécanique des déchets contenant des substances dangereuses",
    )
    WASTE_19_12_12 = (
        "19 12 12",
        "19 12 12 - autres déchets (y compris mélanges) provenant du traitement mécanique des déchets autres que ceux visés à la rubrique 19 12 11",
    )
    WASTE_19_13_01 = (
        "19 13 01*",
        "19 13 01* - déchets solides provenant de la décontamination des sols contenant des substances dangereuses",
    )
    WASTE_19_13_02 = (
        "19 13 02",
        "19 13 02 - déchets solides provenant de la décontamination des sols autres que ceux visés à la rubrique 19 13 01",
    )
    WASTE_19_13_03 = (
        "19 13 03*",
        "19 13 03* - boues provenant de la décontamination des sols contenant des substances dangereuses",
    )
    WASTE_19_13_04 = (
        "19 13 04",
        "19 13 04 - boues provenant de la décontamination des sols autres que celles visées à la rubrique 19 13 03",
    )
    WASTE_19_13_05 = (
        "19 13 05*",
        "19 13 05* - boues provenant de la décontamination des eaux souterraines contenant des substances dangereuses",
    )
    WASTE_19_13_06 = (
        "19 13 06",
        "19 13 06 - boues provenant de la décontamination des eaux souterraines autres que celles visées à la rubrique 19 13 05",
    )
    WASTE_19_13_07 = (
        "19 13 07*",
        "19 13 07* - déchets liquides aqueux et concentrés aqueux provenant de la décontamination des eaux souterraines contenant des substances dangereuses",
    )
    WASTE_19_13_08 = (
        "19 13 08",
        "19 13 08 - déchets liquides aqueux et concentrés aqueux provenant de la décontamination des eaux souterraines autres que ceux visés à la rubrique 19 13 07",
    )
    WASTE_20_01_01 = "20 01 01", "20 01 01 - papier et carton"
    WASTE_20_01_02 = "20 01 02", "20 01 02 - verre"
    WASTE_20_01_08 = "20 01 08", "20 01 08 - déchets de cuisine et de cantine biodégradables"
    WASTE_20_01_10 = "20 01 10", "20 01 10 - vêtements"
    WASTE_20_01_11 = "20 01 11", "20 01 11 - textiles"
    WASTE_20_01_13 = "20 01 13*", "20 01 13* - solvants"
    WASTE_20_01_14 = "20 01 14*", "20 01 14* - acides"
    WASTE_20_01_15 = "20 01 15*", "20 01 15* - déchets basiques"
    WASTE_20_01_17 = "20 01 17*", "20 01 17* - produits chimiques de la photographie"
    WASTE_20_01_19 = "20 01 19*", "20 01 19* - pesticides"
    WASTE_20_01_21 = "20 01 21*", "20 01 21* - tubes fluorescents et autres déchets contenant du mercure"
    WASTE_20_01_23 = "20 01 23*", "20 01 23* - équipements mis au rebut contenant des chlorofluorocarbones"
    WASTE_20_01_25 = "20 01 25", "20 01 25 - huiles et matières grasses alimentaires"
    WASTE_20_01_26 = (
        "20 01 26*",
        "20 01 26* - huiles et matières grasses autres que celles visées à la rubrique 20 01 25",
    )
    WASTE_20_01_27 = (
        "20 01 27*",
        "20 01 27* - peinture, encres, colles et résines contenant des substances dangereuses",
    )
    WASTE_20_01_28 = (
        "20 01 28",
        "20 01 28 - peinture, encres, colles et résines autres que celles visées à la rubrique 20 01 27",
    )
    WASTE_20_01_29 = "20 01 29*", "20 01 29* - détergents contenant des substances dangereuses"
    WASTE_20_01_30 = "20 01 30", "20 01 30 - détergents autres que ceux visés à la rubrique 20 01 29"
    WASTE_20_01_31 = "20 01 31*", "20 01 31* - médicaments cytotoxiques et cytostatiques"
    WASTE_20_01_32 = "20 01 32", "20 01 32 - médicaments autres que ceux visés à la rubrique 20 01 31"
    WASTE_20_01_33 = (
        "20 01 33*",
        "20 01 33* - piles et accumulateurs visés aux rubriques 16 06 01, 16 06 02 ou 16 06 03 et piles et accumulateurs non triés contenant ces piles",
    )
    WASTE_20_01_34 = "20 01 34", "20 01 34 - piles et accumulateurs autres que ceux visés à la rubrique 20 01 33"
    WASTE_20_01_35 = (
        "20 01 35*",
        "20 01 35* - équipements électriques et électroniques mis au rebut contenant des composants dangereux, autres que ceux visés aux rubriques 20 01 21 et 20 01 23 (3)",
    )
    WASTE_20_01_36 = (
        "20 01 36",
        "20 01 36 - équipements électriques et électroniques mis au rebut autres que ceux visés aux rubriques 20 01 21, 20 01 23 et 20 01 35",
    )
    WASTE_20_01_37 = "20 01 37*", "20 01 37* - bois contenant des substances dangereuses"
    WASTE_20_01_38 = "20 01 38", "20 01 38 - bois autres que ceux visés à la rubrique 20 01 37"
    WASTE_20_01_39 = "20 01 39", "20 01 39 - matières plastiques"
    WASTE_20_01_40 = "20 01 40", "20 01 40 - métaux"
    WASTE_20_01_41 = "20 01 41", "20 01 41 - déchets provenant du ramonage de cheminée"
    WASTE_20_01_99 = "20 01 99", "20 01 99 - autres fractions non spécifiées ailleurs"
    WASTE_20_02_01 = "20 02 01", "20 02 01 - déchets biodégradables"
    WASTE_20_02_02 = "20 02 02", "20 02 02 - terres et pierres"
    WASTE_20_02_03 = "20 02 03", "20 02 03 - autres déchets non biodégradables"
    WASTE_20_03_01 = "20 03 01", "20 03 01 - déchets municipaux en mélange"
    WASTE_20_03_02 = "20 03 02", "20 03 02 - déchets de marchés"
    WASTE_20_03_03 = "20 03 03", "20 03 03 - déchets de nettoyage des rues"
    WASTE_20_03_04 = "20 03 04", "20 03 04 - boues de fosses septiques"
    WASTE_20_03_06 = "20 03 06", "20 03 06 - déchets provenant du nettoyage des égouts"
    WASTE_20_03_07 = "20 03 07", "20 03 07 - déchets encombrants"
    WASTE_20_03_99 = "20 03 99", "20 03 99 - déchets municipaux non spécifiés ailleurs"


class RegistryV2WasteCode__(models.TextChoices):
    """European Waste Catalogue codes with descriptions."""

    WASTE_01_01_01 = "01 01 01", "01 01 01 - déchets provenant de l'extraction des minéraux métallifères"
    WASTE_01_01_02 = "01 01 02", "01 01 02 - déchets provenant de l'extraction des minéraux non métallifères"
    WASTE_01_03_04 = "01 03 04*", "01 03 04* - stériles acidogènes provenant de la transformation du sulfure"
    WASTE_01_03_05 = "01 03 05*", "01 03 05* - autres stériles contenant des substances dangereuses"
    WASTE_01_03_06 = "01 03 06", "01 03 06 - stériles autres que ceux visés aux rubriques 01 03 04 et 01 03 05"
    WASTE_01_03_07 = (
        "01 03 07*",
        "01 03 07* - autres déchets contenant des substances dangereuses provenant de la transformation physique et chimique des minéraux métallifères",
    )
    WASTE_01_03_08 = (
        "01 03 08",
        "01 03 08 - déchets de poussières et de poudres autres que ceux visés à la rubrique 01 03 07",
    )
    WASTE_01_03_09 = (
        "01 03 09",
        "01 03 09 - boues rouges issues de la production d'alumine autres que celles visées à la rubrique 01 03 10",
    )
    WASTE_01_03_10 = (
        "01 03 10*",
        "01 03 10* - boues rouges issues de la production d'alumine contenant des substances dangereuses, autres que les déchets visés à la rubrique 01 03 07",
    )
    WASTE_01_03_99 = "01 03 99", "01 03 99 - déchets non spécifiés ailleurs"
    WASTE_01_04_07 = (
        "01 04 07*",
        "01 04 07* - déchets contenant des substances dangereuses provenant de la transformation physique et chimique des minéraux non métallifères",
    )
    WASTE_01_04_08 = (
        "01 04 08",
        "01 04 08 - déchets de graviers et débris de pierres autres que ceux visés à la rubrique 01 04 07",
    )
    WASTE_01_04_09 = "01 04 09", "01 04 09 - déchets de sable et d'argile"
    WASTE_01_04_10 = (
        "01 04 10",
        "01 04 10 - déchets de poussières et de poudres autres que ceux visés à la rubrique 01 04 07",
    )
    WASTE_01_04_11 = (
        "01 04 11",
        "01 04 11 - déchets de la transformation de la potasse et des sels minéraux autres que ceux visés à la rubrique 01 04 07",
    )
    WASTE_01_04_12 = (
        "01 04 12",
        "01 04 12 - stériles et autres déchets provenant du lavage et du nettoyage des minéraux autres que ceux visés aux rubriques 01 04 07 et 01 04 11",
    )
    WASTE_01_04_13 = (
        "01 04 13",
        "01 04 13 - déchets provenant de la taille et du sciage des pierres autres que ceux visés à la rubrique 01 04 07",
    )
    WASTE_01_04_99 = "01 04 99", "01 04 99 - déchets non spécifiés ailleurs"
    WASTE_01_05_04 = "01 05 04", "01 05 04 - boues et autres déchets de forage à l'eau douce"
    WASTE_01_05_05 = "01 05 05*", "01 05 05* - boues et autres déchets de forage contenant des hydrocarbures"
    WASTE_01_05_06 = (
        "01 05 06*",
        "01 05 06* - boues de forage et autres déchets de forage contenant des substances dangereuses",
    )
    WASTE_01_05_07 = (
        "01 05 07",
        "01 05 07 - boues et autres déchets de forage contenant des sels de baryum, autres que ceux visés aux rubriques 01 05 05 et 01 05 06",
    )
    WASTE_01_05_08 = (
        "01 05 08",
        "01 05 08 - boues et autres déchets de forage contenant des chlorures, autres que ceux visés aux rubriques 01 05 05 et 01 05 06",
    )
    WASTE_01_05_99 = "01 05 99", "01 05 99 - déchets non spécifiés ailleurs"
    WASTE_02_01_01 = "02 01 01", "02 01 01 - boues provenant du lavage et du nettoyage"
    WASTE_02_01_02 = "02 01 02", "02 01 02 - déchets de tissus animaux"
    WASTE_02_01_03 = "02 01 03", "02 01 03 - déchets de tissus végétaux"
    WASTE_02_01_04 = "02 01 04", "02 01 04 - déchets de matières plastiques (à l'exclusion des emballages)"
    WASTE_02_01_06 = (
        "02 01 06",
        "02 01 06 - fèces, urine et fumier (y compris paille souillée), effluents, collectés séparément et traités hors site",
    )
    WASTE_02_01_07 = "02 01 07", "02 01 07 - déchets provenant de la sylviculture"
    WASTE_02_01_08 = "02 01 08*", "02 01 08* - déchets agrochimiques contenant des substances dangereuses"
    WASTE_02_01_09 = "02 01 09", "02 01 09 - déchets agrochimiques autres que ceux visés à la rubrique 02 01 08"
    WASTE_02_01_10 = "02 01 10", "02 01 10 - déchets métalliques"
    WASTE_02_01_99 = "02 01 99", "02 01 99 - déchets non spécifiés ailleurs"
    WASTE_02_02_01 = "02 02 01", "02 02 01 - boues provenant du lavage et du nettoyage"
    WASTE_02_02_02 = "02 02 02", "02 02 02 - déchets de tissus animaux"
    WASTE_02_02_03 = "02 02 03", "02 02 03 - matières impropres à la consommation ou à la transformation"
    WASTE_02_02_04 = "02 02 04", "02 02 04 - boues provenant du traitement in situ des effluents"
    WASTE_02_02_99 = "02 02 99", "02 02 99 - déchets non spécifiés ailleurs"
    WASTE_02_03_01 = (
        "02 03 01",
        "02 03 01 - boues provenant du lavage, du nettoyage, de l'épluchage, de la centrifugation et de la séparation",
    )
    WASTE_02_03_02 = "02 03 02", "02 03 02 - déchets d'agents de conservation"
    WASTE_02_03_03 = "02 03 03", "02 03 03 - déchets de l'extraction aux solvants"
    WASTE_02_03_04 = "02 03 04", "02 03 04 - matières impropres à la consommation ou à la transformation"
    WASTE_02_03_05 = "02 03 05", "02 03 05 - boues provenant du traitement in situ des effluents"
    WASTE_02_03_99 = "02 03 99", "02 03 99 - déchets non spécifiés ailleurs"
    WASTE_02_04_01 = "02 04 01", "02 04 01 - terre provenant du lavage et du nettoyage des betteraves"
    WASTE_02_04_02 = "02 04 02", "02 04 02 - carbonate de calcium déclassé"
    WASTE_02_04_03 = "02 04 03", "02 04 03 - boues provenant du traitement in situ des effluents"
    WASTE_02_04_99 = "02 04 99", "02 04 99 - déchets non spécifiés ailleurs"
    WASTE_02_05_01 = "02 05 01", "02 05 01 - matières impropres à la consommation ou à la transformation"
    WASTE_02_05_02 = "02 05 02", "02 05 02 - boues provenant du traitement in situ des effluents"
    WASTE_02_05_99 = "02 05 99", "02 05 99 - déchets non spécifiés ailleurs"
    WASTE_02_06_01 = "02 06 01", "02 06 01 - matières impropres à la consommation ou à la transformation"
    WASTE_02_06_02 = "02 06 02", "02 06 02 - déchets d'agents de conservation"
    WASTE_02_06_03 = "02 06 03", "02 06 03 - boues provenant du traitement in situ des effluents"
    WASTE_02_06_99 = "02 06 99", "02 06 99 - déchets non spécifiés ailleurs"
    WASTE_02_07_01 = (
        "02 07 01",
        "02 07 01 - déchets provenant du lavage, du nettoyage et de la réduction mécanique des matières premières",
    )
    WASTE_02_07_02 = "02 07 02", "02 07 02 - déchets de la distillation de l'alcool"
    WASTE_02_07_03 = "02 07 03", "02 07 03 - déchets de traitements chimiques"
    WASTE_02_07_04 = "02 07 04", "02 07 04 - matières impropres à la consommation ou à la transformation"
    WASTE_02_07_05 = "02 07 05", "02 07 05 - boues provenant du traitement in situ des effluents"
    WASTE_02_07_99 = "02 07 99", "02 07 99 - déchets non spécifiés ailleurs"
    WASTE_03_01_01 = "03 01 01", "03 01 01 - déchets d'écorce et de liège"
    WASTE_03_01_04 = (
        "03 01 04*",
        "03 01 04* - sciure de bois, copeaux, chutes, bois, panneaux de particules et placages contenant des substances dangereuses",
    )
    WASTE_03_01_05 = (
        "03 01 05",
        "03 01 05 - sciure de bois, copeaux, chutes, bois, panneaux de particules et placages autres que ceux visés à la rubrique 03 01 04",
    )
    WASTE_03_01_99 = "03 01 99", "03 01 99 - déchets non spécifiés ailleurs"
    WASTE_03_02_01 = "03 02 01*", "03 02 01* - composés organiques non halogénés de protection du bois"
    WASTE_03_02_02 = "03 02 02*", "03 02 02* - composés organochlorés de protection du bois"
    WASTE_03_02_03 = "03 02 03*", "03 02 03* - composés organométalliques de protection du bois"
    WASTE_03_02_04 = "03 02 04*", "03 02 04* - composés inorganiques de protection du bois"
    WASTE_03_02_05 = (
        "03 02 05*",
        "03 02 05* - autres produits de protection du bois contenant des substances dangereuses",
    )
    WASTE_03_02_99 = "03 02 99", "03 02 99 - produits de protection du bois non spécifiés ailleurs"
    WASTE_03_03_01 = "03 03 01", "03 03 01 - déchets d'écorce et de bois"
    WASTE_03_03_02 = "03 03 02", "03 03 02 - liqueurs vertes (provenant de la récupération de liqueur de cuisson)"
    WASTE_03_03_05 = "03 03 05", "03 03 05 - boues de désencrage provenant du recyclage du papier"
    WASTE_03_03_07 = (
        "03 03 07",
        "03 03 07 - refus séparés mécaniquement provenant du broyage de déchets de papier et de carton",
    )
    WASTE_03_03_08 = "03 03 08", "03 03 08 - déchets provenant du tri de papier et de carton destinés au recyclage"
    WASTE_03_03_09 = "03 03 09", "03 03 09 - déchets de boues résiduaires de chaux"
    WASTE_03_03_10 = (
        "03 03 10",
        "03 03 10 - refus fibreux, boues de fibres, de charge et de couchage provenant d'une séparation mécanique",
    )
    WASTE_03_03_11 = (
        "03 03 11",
        "03 03 11 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 03 03 10",
    )
    WASTE_03_03_99 = "03 03 99", "03 03 99 - déchets non spécifiés ailleurs"
    WASTE_04_01_01 = "04 01 01", "04 01 01 - déchets d'écharnage et refentes"
    WASTE_04_01_02 = "04 01 02", "04 01 02 - résidus de pelanage"
    WASTE_04_01_03 = "04 01 03*", "04 01 03* - déchets de dégraissage contenant des solvants sans phase liquide"
    WASTE_04_01_04 = "04 01 04", "04 01 04 - liqueur de tannage contenant du chrome"
    WASTE_04_01_05 = "04 01 05", "04 01 05 - liqueur de tannage sans chrome"
    WASTE_04_01_06 = (
        "04 01 06",
        "04 01 06 - boues, notamment provenant du traitement in situ des effluents, contenant du chrome",
    )
    WASTE_04_01_07 = (
        "04 01 07",
        "04 01 07 - boues, notamment provenant du traitement in situ des effluents, sans chrome",
    )
    WASTE_04_01_08 = (
        "04 01 08",
        "04 01 08 - déchets de cuir tanné (refentes sur bleu, dérayures, échantillonnages, poussières de ponçage), contenant du chrome",
    )
    WASTE_04_01_09 = "04 01 09", "04 01 09 - déchets provenant de l'habillage et des finitions"
    WASTE_04_01_99 = "04 01 99", "04 01 99 - déchets non spécifiés ailleurs"
    WASTE_04_02_09 = "04 02 09", "04 02 09 - matériaux composites (textile imprégné, élastomère, plastomère)"
    WASTE_04_02_10 = (
        "04 02 10",
        "04 02 10 - matières organiques issues de produits naturels (par exemple graisse, cire)",
    )
    WASTE_04_02_14 = "04 02 14*", "04 02 14* - déchets provenant des finitions contenant des solvants organiques"
    WASTE_04_02_15 = (
        "04 02 15",
        "04 02 15 - déchets provenant des finitions autres que ceux visés à la rubrique 04 02 14",
    )
    WASTE_04_02_16 = "04 02 16*", "04 02 16* - teintures et pigments contenant des substances dangereuses"
    WASTE_04_02_17 = "04 02 17", "04 02 17 - teintures et pigments autres que ceux visés à la rubrique 04 02 16"
    WASTE_04_02_19 = (
        "04 02 19*",
        "04 02 19* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_04_02_20 = (
        "04 02 20",
        "04 02 20 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 04 02 19",
    )
    WASTE_04_02_21 = "04 02 21", "04 02 21 - fibres textiles non ouvrées"
    WASTE_04_02_22 = "04 02 22", "04 02 22 - fibres textiles ouvrées"
    WASTE_04_02_99 = "04 02 99", "04 02 99 - déchets non spécifiés ailleurs"
    WASTE_05_01_02 = "05 01 02*", "05 01 02* - boues de dessalage"
    WASTE_05_01_03 = "05 01 03*", "05 01 03* - boues de fond de cuves"
    WASTE_05_01_04 = "05 01 04*", "05 01 04* - boues d'alkyles acides"
    WASTE_05_01_05 = "05 01 05*", "05 01 05* - hydrocarbures accidentellement répandus"
    WASTE_05_01_06 = (
        "05 01 06*",
        "05 01 06* - boues contenant des hydrocarbures provenant des opérations de maintenance de l'installation ou des équipements",
    )
    WASTE_05_01_07 = "05 01 07*", "05 01 07* - goudrons acides"
    WASTE_05_01_08 = "05 01 08*", "05 01 08* - autres goudrons"
    WASTE_05_01_09 = (
        "05 01 09*",
        "05 01 09* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_05_01_10 = (
        "05 01 10",
        "05 01 10 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 05 01 09",
    )
    WASTE_05_01_11 = "05 01 11*", "05 01 11* - déchets provenant du nettoyage d'hydrocarbures avec des bases"
    WASTE_05_01_12 = "05 01 12*", "05 01 12* - hydrocarbures contenant des acides"
    WASTE_05_01_13 = "05 01 13", "05 01 13 - boues du traitement de l'eau d'alimentation des chaudières"
    WASTE_05_01_14 = "05 01 14", "05 01 14 - déchets provenant des colonnes de refroidissement"
    WASTE_05_01_15 = "05 01 15*", "05 01 15* - argiles de filtration usées"
    WASTE_05_01_16 = "05 01 16", "05 01 16 - déchets contenant du soufre provenant de la désulfuration du pétrole"
    WASTE_05_01_17 = "05 01 17", "05 01 17 - mélanges bitumineux"
    WASTE_05_01_99 = "05 01 99", "05 01 99 - déchets non spécifiés ailleurs"
    WASTE_05_06_01 = "05 06 01*", "05 06 01* - goudrons acides"
    WASTE_05_06_03 = "05 06 03*", "05 06 03* - autres goudrons"
    WASTE_05_06_04 = "05 06 04", "05 06 04 - déchets provenant des colonnes de refroidissement"
    WASTE_05_06_99 = "05 06 99", "05 06 99 - déchets non spécifiés ailleurs"
    WASTE_05_07_01 = "05 07 01*", "05 07 01* - déchets contenant du mercure"
    WASTE_05_07_02 = "05 07 02", "05 07 02 - déchets contenant du soufre"
    WASTE_05_07_99 = "05 07 99", "05 07 99 - déchets non spécifiés ailleurs"
    WASTE_06_01_01 = "06 01 01*", "06 01 01* - acide sulfurique et acide sulfureux"
    WASTE_06_01_02 = "06 01 02*", "06 01 02* - acide chlorhydrique"
    WASTE_06_01_03 = "06 01 03*", "06 01 03* - acide fluorhydrique"
    WASTE_06_01_04 = "06 01 04*", "06 01 04* - acide phosphorique et acide phosphoreux"
    WASTE_06_01_05 = "06 01 05*", "06 01 05* - acide nitrique et acide nitreux"
    WASTE_06_01_06 = "06 01 06*", "06 01 06* - autres acides"
    WASTE_06_01_99 = "06 01 99", "06 01 99 - déchets non spécifiés ailleurs"
    WASTE_06_02_01 = "06 02 01*", "06 02 01* - hydroxyde de calcium"
    WASTE_06_02_03 = "06 02 03*", "06 02 03* - hydroxyde d'ammonium"
    WASTE_06_02_04 = "06 02 04*", "06 02 04* - hydroxyde de sodium et hydroxyde de potassium"
    WASTE_06_02_05 = "06 02 05*", "06 02 05* - autres bases"
    WASTE_06_02_99 = "06 02 99", "06 02 99 - déchets non spécifiés ailleurs"
    WASTE_06_03_11 = "06 03 11*", "06 03 11* - sels et solutions contenant des cyanures"
    WASTE_06_03_13 = "06 03 13*", "06 03 13* - sels et solutions contenant des métaux lourds"
    WASTE_06_03_14 = (
        "06 03 14",
        "06 03 14 - sels solides et solutions autres que ceux visés aux rubriques 06 03 11 et 06 03 13",
    )
    WASTE_06_03_15 = "06 03 15*", "06 03 15* - oxydes métalliques contenant des métaux lourds"
    WASTE_06_03_16 = "06 03 16", "06 03 16 - oxydes métalliques autres que ceux visés à la rubrique 06 03 15"
    WASTE_06_03_99 = "06 03 99", "06 03 99 - déchets non spécifiés ailleurs"
    WASTE_06_04_03 = "06 04 03*", "06 04 03* - déchets contenant de l'arsenic"
    WASTE_06_04_04 = "06 04 04*", "06 04 04* - déchets contenant du mercure"
    WASTE_06_04_05 = "06 04 05*", "06 04 05* - déchets contenant d'autres métaux lourds"
    WASTE_06_04_99 = "06 04 99", "06 04 99 - déchets non spécifiés ailleurs"
    WASTE_06_05_02 = (
        "06 05 02*",
        "06 05 02* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_06_05_03 = (
        "06 05 03",
        "06 05 03 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 06 05 02",
    )
    WASTE_06_06_02 = "06 06 02*", "06 06 02* - déchets contenant des sulfures dangereux"
    WASTE_06_06_03 = (
        "06 06 03",
        "06 06 03 - déchets contenant des sulfures autres que ceux visés à la rubrique 06 06 02",
    )
    WASTE_06_06_99 = "06 06 99", "06 06 99 - déchets non spécifiés ailleurs"
    WASTE_06_07_01 = "06 07 01*", "06 07 01* - déchets contenant de l'amiante provenant de l'électrolyse"
    WASTE_06_07_02 = "06 07 02*", "06 07 02* - déchets de charbon actif utilisé pour la production du chlore"
    WASTE_06_07_03 = "06 07 03*", "06 07 03* - boues de sulfate de baryum contenant du mercure"
    WASTE_06_07_04 = "06 07 04*", "06 07 04* - solutions et acides, par exemple acide de contact"
    WASTE_06_07_99 = "06 07 99", "06 07 99 - déchets non spécifiés ailleurs"
    WASTE_06_08_02 = "06 08 02*", "06 08 02* - déchets contenant des chlorosilanes dangereux"
    WASTE_06_08_99 = "06 08 99", "06 08 99 - déchets non spécifiés ailleurs"
    WASTE_06_09_02 = "06 09 02", "06 09 02 - scories phosphoriques"
    WASTE_06_09_03 = (
        "06 09 03*",
        "06 09 03* - déchets de réactions basées sur le calcium contenant des substances dangereuses ou contaminées par de telles substances",
    )
    WASTE_06_09_04 = (
        "06 09 04",
        "06 09 04 - déchets de réactions basées sur le calcium autres que ceux visés à la rubrique 06 09 03",
    )
    WASTE_06_09_99 = "06 09 99", "06 09 99 - déchets non spécifiés ailleurs"
    WASTE_06_10_02 = "06 10 02*", "06 10 02* - déchets contenant des substances dangereuses"
    WASTE_06_10_99 = "06 10 99", "06 10 99 - déchets non spécifiés ailleurs"
    WASTE_06_11_01 = (
        "06 11 01",
        "06 11 01 - déchets de réactions basées sur le calcium provenant de la production de dioxyde de titane",
    )
    WASTE_06_11_99 = "06 11 99", "06 11 99 - déchets non spécifiés ailleurs"
    WASTE_06_13_01 = (
        "06 13 01*",
        "06 13 01* - produits phytosanitaires inorganiques, agents de protection du bois et autres biocides",
    )
    WASTE_06_13_02 = "06 13 02*", "06 13 02* - charbon actif usé (sauf rubrique 06 07 02)"
    WASTE_06_13_03 = "06 13 03", "06 13 03 - noir de carbone"
    WASTE_06_13_04 = "06 13 04*", "06 13 04* - déchets provenant de la transformation de l'amiante"
    WASTE_06_13_05 = "06 13 05*", "06 13 05* - suies"
    WASTE_06_13_99 = "06 13 99", "06 13 99 - déchets non spécifiés ailleurs"
    WASTE_07_01_01 = "07 01 01*", "07 01 01* - eaux de lavage et liqueurs mères aqueuses"
    WASTE_07_01_03 = "07 01 03*", "07 01 03* - solvants, liquides de lavage et liqueurs mères organiques halogénés"
    WASTE_07_01_04 = "07 01 04*", "07 01 04* - autres solvants, liquides de lavage et liqueurs mères organiques"
    WASTE_07_01_07 = "07 01 07*", "07 01 07* - résidus de réaction et résidus de distillation halogénés"
    WASTE_07_01_08 = "07 01 08*", "07 01 08* - autres résidus de réaction et résidus de distillation"
    WASTE_07_01_09 = "07 01 09*", "07 01 09* - gâteaux de filtration et absorbants usés halogénés"
    WASTE_07_01_10 = "07 01 10*", "07 01 10* - autres gâteaux de filtration et absorbants usés"
    WASTE_07_01_11 = (
        "07 01 11*",
        "07 01 11* - boues provenant du traitement in situ des effluents contenant des substances dangereuses",
    )
    WASTE_07_01_12 = (
        "07 01 12",
        "07 01 12 - boues provenant du traitement in situ des effluents autres que celles visées à la rubrique 07 01 11",
    )
