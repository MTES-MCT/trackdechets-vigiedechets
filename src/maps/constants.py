BASE_ROLES_TYPES = ["emitter", "transporter", "destination"]

BSDD = "bsdd"
BSDND = "bsdnd"
BSDA = "bsda"
BSDASRI = "bsdasri"
BSFF = "bsff"
BSVHU = "bsvhu"
TEXS = "texs"
TEXS_DD = "texs_dd"
DND = "dnd"
SSD = "ssd"


ROLES_CONFIG = {
    BSDD: {"roles": BASE_ROLES_TYPES, "code_operation": True},
    BSDND: {"roles": BASE_ROLES_TYPES, "code_operation": True},
    BSDA: {"roles": ["emitter", "transporter", "destination", "worker"], "code_operation": True},
    BSFF: {"roles": BASE_ROLES_TYPES, "code_operation": True},
    BSDASRI: {"roles": BASE_ROLES_TYPES, "code_operation": True},
    BSVHU: {"roles": BASE_ROLES_TYPES, "code_operation": True},
    TEXS_DD: {"roles": BASE_ROLES_TYPES, "code_operation": True},
    TEXS: {"roles": ["emitter", "destination"], "code_operation": True},
    DND: {"roles": ["emitter", "destination"], "code_operation": True},
    SSD: {"roles": [], "code_operation": False},
}

ROLES_TYPES = {bsd_type: config["roles"] for bsd_type, config in ROLES_CONFIG.items()}

WASTE_NAMES = [
    "Déchets dangereux",
    "Amiante",
    "Fluides Frigorigènes",
    "Dasri",
    "Vehicules hors d'usage",
    "Sortie de statut de déchet",
    "Déchets non dangereux",
    "Terres et sédiments - DD",
    "Terres et sédiments - DND",
]

PROCESSING_OPERATIONS_FIELDS = [
    "processing_operations_bsdd",
    "processing_operations_bsdnd",
    "processing_operations_bsda",
    "processing_operations_bsff",
    "processing_operations_bsdasri",
    "processing_operations_bsvhu",
    "processing_operations_dnd",
    "processing_operations_texs",
]

ANNUAL_ICPE_RUBRIQUES = ["2760-1", "2760-2"]  # unité t/an
DAILY_ICPE_RUBRIQUES = ["2790", "2791","2770", "2771"]  # unité t/jour

ICPE_RUBRIQUES = ANNUAL_ICPE_RUBRIQUES + DAILY_ICPE_RUBRIQUES

BSD_TYPES = [
    "bsdd",
    "bsdnd",
    "bsda",
    "bsff",
    "bsdasri",
    "bsvhu",
    "texs_dd",
    "dnd",
    "texs",
]

MIN_TGAP_INFO_YEAR = 2024
