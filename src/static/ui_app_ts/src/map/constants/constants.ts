import { Profile, SubProfile } from "../types";

export const TYPE_AND_ROLE = "TYPE_AND_ROLE";
export const WASTE_CODE = "WASTE_CODE";

export const ZOOM_ETABS = 9;
export const ZOOM_CLUSTERS = 8;
export const MAX_ETAB_FOR_DOWNLOAD = 1500;

const broker = "BROKER";
/** Installation de Tri, transit regroupement de déchets */
const collector = "COLLECTOR";

/** Installation de valorisation de terres et sédiments */
const disposalfacility = "DISPOSAL_FACILITY";
/** Éco-organisme */
const ecoorganisme = "ECO_ORGANISME";
/** Intermédiaire : établissement qui peut être ajouté à une traçabilité, sans responsabilité réglementaire (y compris entreprises de travaux hors amiante) */
const intermediary = "INTERMEDIARY";
/** Producteur de déchet */
const producer = "PRODUCER";
/** Installation dans laquelle les déchets perdent leur statut de déchet */
const recoveryfacility = "RECOVERY_FACILITY";
/** Négociant */
const trader = "TRADER";
/** Transporteur */
const transporter = "TRANSPORTER";
/** Installation de traitement */
const wasteprocessor = "WASTEPROCESSOR";
/** Installation de collecte de déchets apportés par le producteur initial (Rubrique 2710) */
const wastecenter = "WASTE_CENTER";
/** Installation de traitement de VHU (casse automobile et/ou broyeur agréé) */
const wastevehicles = "WASTE_VEHICLES";
/** Entreprise de travaux */
const worker = "WORKER";

export const BSDD = "BSDD";
export const BSDND = "BSDND";
export const BSDA = "BSDA";
export const BSDASRI = "BSDASRI";
export const BSFF = "BSFF";
export const BSVHU = "BSVHU";
export const TEXS = "TEXS";
export const TEXS_DD = "TEXS_DD";
export const SSD = "SSD";

export const VERBOSE_BSD_TYPES = {
  [BSDD]: "Bsdd",
  [BSDND]: "Bsdnd",
  [BSDA]: "Bsda",
  [BSDASRI]: "Bsdasri",
  [BSFF]: "Bsff",
  [BSVHU]: "Bsvhu",
  [TEXS]: "T. Exc.",
  [TEXS_DD]: "T. Exc. DD",
  [SSD]: "Ssd",
};

export const ROLE_EMITTER = "emitter";
export const ROLE_TRANSPORTER = "transporter";
export const ROLE_WORKER = "worker";
export const ROLE_DESTINATION = "destination";

export const VERBOSE_ROLES = {
  [ROLE_EMITTER]: "Producteur",
  [ROLE_TRANSPORTER]: "Transporteur",
  [ROLE_WORKER]: "Entreprise de travaux",
  [ROLE_DESTINATION]: "Destinataire",
};
const CollectorType = {
  /** Déchets Dangereux (Rubrique 2718) */
  DangerousWastes: "DANGEROUS_WASTES",
  /** Déchets DEEE (Rubrique 2711) */
  DeeeWastes: "DEEE_WASTES",
  /** Déchets non Dangereux (Rubriques 2713, 2714, 2715, 2716) */
  NonDangerousWastes: "NON_DANGEROUS_WASTES",
  /** Autres cas déchets dangereux (Rubriques 2719, 2792-1, 2793-1, 2793-2, 2797-1, 2798) */
  OtherDangerousWastes: "OTHER_DANGEROUS_WASTES",
  /** Autres cas déchets non dangereux (Rubrique 2731) */
  OtherNonDangerousWastes: "OTHER_NON_DANGEROUS_WASTES",
};
const WasteProcessorType = {
  /** Crémation */
  Cremation: "CREMATION",
  /** Incinération de déchets dangereux (Rubrique 2770) */
  DangerousWastesIncineration: "DANGEROUS_WASTES_INCINERATION",
  /** Installation de stockage de déchets dangereux (Rubriques 2720-1, 2760-1, 2760-4, 2797-2) */
  DangerousWastesStorage: "DANGEROUS_WASTES_STORAGE",
  /** Installation de stockage de déchets inertes (Rubrique 2760-3) */
  InertWastesStorage: "INERT_WASTES_STORAGE",
  /** Incinération de déchets non dangereux (Rubriques 2771, 2740) */
  NonDangerousWastesIncineration: "NON_DANGEROUS_WASTES_INCINERATION",
  /** Installation de stockage de déchets non dangereux, y compris casiers dédiés amiante, plâtre (Rubriques 2720-2, 2760-2-a, 2760-2-b) */
  NonDangerousWastesStorage: "NON_DANGEROUS_WASTES_STORAGE",
  /** Autres traitements de déchets dangereux (Rubriques 2790, 2792-2, 2793-3) */
  OtherDangerousWastes: "OTHER_DANGEROUS_WASTES",
  /** Autres traitements de déchets non dangereux (Rubriques 2791, 2781, 2782, 2780) */
  OtherNonDangerousWastes: "OTHER_NON_DANGEROUS_WASTES",
};

export const COLLECTOR_TYPE_OPTIONS: SubProfile[] = [
  {
    label: "Déchets non Dangereux (Rubriques 2713, 2714, 2715, 2716)",
    shortLabel: "Déchets non Dangereux",
    value: CollectorType.NonDangerousWastes,
  },
  {
    label: "Déchets Dangereux (Rubrique 2718)",
    value: CollectorType.DangerousWastes,

    shortLabel: "Déchets Dangereux",
  },
  {
    label: "Déchets DEEE (Rubrique 2711)",
    value: CollectorType.DeeeWastes,
    shortLabel: "Déchets DEEE",
  },
  {
    label: "Autres cas déchets non dangereux (Rubrique 2731)",
    value: CollectorType.OtherNonDangerousWastes,
    shortLabel: "Autres déchets non dangereux",
  },
  {
    label:
      "Autres cas déchets dangereux (Rubriques 2719, 2792-1, 2793-1, 2793-2, 2797-1, 2798)",
    value: CollectorType.OtherDangerousWastes,
    shortLabel: "Autres déchets dangereux",
  },
];

export const WASTE_PROCESSOR_TYPE_OPTIONS: SubProfile[] = [
  {
    label: "Incinération de déchets dangereux (Rubrique 2770)",
    shortLabel: "Incinération dd",
    value: WasteProcessorType.DangerousWastesIncineration,
  },
  {
    label: "Incinération de déchets non dangereux (Rubriques 2771, 2740)",
    shortLabel: "Incinération dnd",
    value: WasteProcessorType.NonDangerousWastesIncineration,
  },
  {
    label: "Crémation",
    shortLabel: "Crémation",
    value: WasteProcessorType.Cremation,
  },
  {
    label:
      "Installation de stockage de déchets dangereux (Rubriques 2720-1, 2760-1, 2760-4, 2797-2)",
    shortLabel: "Stockage dd",
    value: WasteProcessorType.DangerousWastesStorage,
  },
  {
    label:
      "Installation de stockage de déchets non dangereux, y compris casiers dédiés amiante, plâtre (Rubriques 2720-2, 2760-2-a, 2760-2-b)",
    shortLabel: "Stockage dnd",
    value: WasteProcessorType.NonDangerousWastesStorage,
  },
  {
    label: "Installation de stockage de déchets inertes (Rubrique 2760-3)",
    shortLabel: "Stockage inerte",
    value: WasteProcessorType.InertWastesStorage,
  },
  {
    label:
      "Autres traitements de déchets non dangereux (Rubriques 2791, 2781, 2782, 2780)",
    shortLabel: "Autres traitements  dnd",
    value: WasteProcessorType.OtherNonDangerousWastes,
  },
  {
    label:
      "Autres traitements de déchets dangereux (Rubriques 2790, 2792-2, 2793-3)",
    shortLabel: "Autres traitements dd",
    value: WasteProcessorType.OtherDangerousWastes,
  },
];

export const WASTE_VEHICLES_TYPE_OPTIONS: SubProfile[] = [
  { label: "Broyeur VHU", shortLabel: "Broyeur VHU", value: "BROYEUR" },
  {
    label: "Casse automobile / démolisseur",
    shortLabel: "Casse auto",
    value: "DEMOLISSEUR",
  },
];
export const SUB_PROFILES: Record<string, SubProfile[]> = {
  collectorTypes: COLLECTOR_TYPE_OPTIONS,
  wasteProcessorTypes: WASTE_PROCESSOR_TYPE_OPTIONS,
  wasteVehiclesTypes: WASTE_VEHICLES_TYPE_OPTIONS,
};

export const PROFILE_OPTIONS: Profile[] = [
  {
    value: producer,
    label: "Producteur de déchets, y compris terres et sédiments",
    shortLabel: "Producteur",
  },
  {
    value: intermediary,
    label: "Intermédiaire",
    shortLabel: "Intermédiaire",
  },
  {
    value: collector,
    label:
      "Installation de Tri, transit regroupement de déchets y compris non classée",
    shortLabel: "TTR",

    options: COLLECTOR_TYPE_OPTIONS,
    subTypesName: "collectorTypes",
  },
  {
    value: wasteprocessor,
    label: "Installation de traitement",
    shortLabel: "Installation de traitement",

    options: WASTE_PROCESSOR_TYPE_OPTIONS,

    subTypesName: "wasteProcessorTypes",
  },
  {
    value: disposalfacility,
    label: "Installation de valorisation de terres et sédiments",
    shortLabel: "Terres et sédiments",
  },
  {
    value: wastecenter,
    label:
      "Installation de collecte de déchets apportés par le producteur initial (Rubrique 2710)",
    shortLabel: "Installation de collecte",
  },
  {
    value: wastevehicles,
    label: "Installation de traitement de VHU",
    shortLabel: "Vhus",

    options: WASTE_VEHICLES_TYPE_OPTIONS,
    subTypesName: "wasteVehiclesTypes",
  },
  {
    value: transporter,
    label: "Transporteur",
    shortLabel: "Transporteur",
  },
  {
    value: trader,
    label: "Négociant",
    shortLabel: "Négociant",
  },
  {
    value: broker,
    label: "Courtier",
    shortLabel: "Courtier",
  },
  {
    value: ecoorganisme,
    label: "Éco-organisme",
    shortLabel: "Éco-organisme",
  },
  {
    value: worker,
    label: "Entreprise de travaux amiante",
    shortLabel: "Travaux amiante",
  },
  {
    value: recoveryfacility,
    label:
      "Installation dans laquelle les déchets perdent leur statut de déchet",
    shortLabel: "Perte statut de déchet",
  },
];

type ProfileMapping = Record<string, string>;

function createProfileMapping() {
  const mapping: ProfileMapping = {};

  PROFILE_OPTIONS.forEach((option) => {
    mapping[option.value] = option.shortLabel;

    if (option.options && option.subTypesName) {
      option.options.forEach((subOption) => {
        mapping[subOption.value] = subOption.shortLabel;
      });
    }
  });

  return mapping;
}

export const PROFILE_MAPPING = createProfileMapping();
