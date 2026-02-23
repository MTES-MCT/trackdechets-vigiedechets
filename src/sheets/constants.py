COMPANY_TYPES = {
    "COLLECTOR": "Tri Transit Regroupement (TTR)",
    "WASTEPROCESSOR": "Usine de traitement",
    "WASTE_CENTER": "Déchetterie",
    "BROKER": "Courtier",
    "TRADER": "Négociant",
    "TRANSPORTER": "Transporteur",
    "ECO_ORGANISM": "Éco-organisme",
    "ECO_ORGANISME": "Éco-organisme",
    "PRODUCER": "Producteur",
    "WASTE_VEHICLES": "Centre Véhicules Hors d'Usage",
    "CREMATORIUM": "Crématorium",
    "WORKER": "Entreprise de travaux",
    "INTERMEDIARY": "Intermédiaire",
    "DISPOSAL_FACILITY": "Installation de valorisation de terres et sédiments",
    "RECOVERY_FACILITY": "Installation dans laquelle les déchets perdent leur statut de déchet",
}

WASTE_PROCESSOR_TYPES = {
    "DANGEROUS_WASTES_INCINERATION": "Incinération de déchets dangereux",
    "NON_DANGEROUS_WASTES_INCINERATION": "Incinération de déchets non dangereux",
    "CREMATION": "Crémation",
    "DANGEROUS_WASTES_STORAGE": "Installation de stockage de déchets dangereux",
    "NON_DANGEROUS_WASTES_STORAGE": "Installation de stockage de déchets non dangereux (y compris casiers dédiés amiante, plâtre)",
    "INERT_WASTES_STORAGE": "Installation de stockage de déchets inertes",
    "OTHER_DANGEROUS_WASTES": "Autres traitements de déchets dangereux",
    "OTHER_NON_DANGEROUS_WASTES": "Autres traitement de déchets non dangereux",
}


COLLECTOR_TYPES = {
    "NON_DANGEROUS_WASTES": "Déchets non Dangereux (Rubriques 2713, 2714, 2715, 2716)",
    "DANGEROUS_WASTES": "Déchets Dangereux (Rubrique 2718)",
    "DEEE_WASTES": "Déchets DEEE (Rubrique 2711)",
    "OTHER_NON_DANGEROUS_WASTES": "Autres cas déchets non dangereux (Rubrique 2731)",
    "OTHER_DANGEROUS_WASTES": "Autres cas déchets dangereux (Rubriques 2719, 2792-1, 2793-1, 2793-2, 2797-1, 2798)",
}

VHU_PROCESSOR_TYPES = {
    "BROYEUR": "Broyeur VHU",
    "DEMOLISSEUR": "Casse automobile / démolisseur",
}

BSDD = "bsdd"
BSDD_NON_DANGEROUS = "bsdd_non_dangerous"
BSDA = "bsda"
BSDASRI = "bsdasri"
BSFF = "bsff"
BSVHU = "bsvhu"

BS_TYPES_WITH_MULTIMODAL_TRANSPORT = [BSDD, BSDD_NON_DANGEROUS, BSDA, BSFF]

DANGEROUS_WASTE = "dangerous"
NON_DANGEROUS_WASTE = "non_dangerous"
AMIANTE_WASTE = "amiante"

WASTE_TYPE_BS_TYPE_MAPPING = {
    DANGEROUS_WASTE: BSDD,
    NON_DANGEROUS_WASTE: BSDD_NON_DANGEROUS,
    AMIANTE_WASTE: BSDA,
}


PLOTLY_GRAPHS_TO_RENDER_IN_PDF = [
    "bsdd_created_rectified",
    "bsdd_stock",
    "bsdd_non_dangerous_created_rectified",
    "bsdd_non_dangerous_stock",
    "bsda_created_rectified",
    "bsda_stock",
    "bsdasri_created_rectified",
    "bsdasri_stock",
    "bsff_created_rectified",
    "bsff_stock",
    "bsvhu_created_rectified",
    "bsvhu_stock",
    "dangerous_waste_origin",
    "non_dangerous_waste_origin",
    "amiante_waste_origin",
    "icpe_2770",
    "icpe_2790",
    "icpe_2760_1",
    "icpe_2771",
    "icpe_2791",
    "icpe_2760_2",
    "bsda_worker_quantity",
    "transporter_bordereaux_stats_graph",
    "quantities_transported_stats_graph",
    "non_dangerous_waste_statements_graph",
    "non_dangerous_waste_quantities_graph",
    "excavated_land_statements_graph",
    "excavated_land_quantities_graph",
    "ssd_statements_graph",
    "ssd_quantities_graph",
    "registry_transporter_statement_stats_graph",
    "registry_transporter_quantities_graph",
    "eco_organisme_bordereaux_graph",
    "eco_organisme_quantities_graph",
]
