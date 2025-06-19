interface ProcessingCodeItem {
  code: string;
  description: string;
}

interface ProcessingCodesMap {
  [key: string]: ProcessingCodeItem;
}

export const PROCESSING_CODES: ProcessingCodesMap = {
  R1: {
    code: "R1",
    description:
      "Utilisation principale comme combustible ou autre moyen de produire de l'énergie",
  },
  R2: {
    code: "R2",
    description: "Récupération ou régénération des solvants",
  },
  R3: {
    code: "R3",
    description:
      "Recyclage ou récupération des substances organiques qui ne sont pas utilisées comme solvants (y compris les opérations de compostage et autres transformations biologiques)",
  },
  R4: {
    code: "R4",
    description:
      "Recyclage ou récupération des métaux et des composés métalliques",
  },
  R5: {
    code: "R5",
    description: "Recyclage ou récupération d'autres matières inorganiques",
  },
  R6: {
    code: "R6",
    description: "Régénération des acides ou des bases",
  },
  R7: {
    code: "R7",
    description: "Récupération des produits servant à capter les polluants",
  },
  R8: {
    code: "R8",
    description: "Récupération des produits provenant des catalyseurs",
  },
  R9: {
    code: "R9",
    description: "Régénération ou autres réemplois des huiles",
  },
  R10: {
    code: "R10",
    description:
      "Épandage sur le sol au profit de l'agriculture ou de l'écologie",
  },
  R11: {
    code: "R11",
    description:
      "Utilisation de déchets résiduels obtenus à partir de l'une des opérations numérotées R1 à R10",
  },
  R12: {
    code: "R12",
    description:
      "Échange de déchets en vue de les soumettre à l'une des opérations numérotées R1 à R11",
  },
  R13: {
    code: "R13",
    description:
      "Stockage de déchets préalablement à l'une des opérations R1 à R12 (à l'exclusion du stockage temporaire, avant collecte, sur le site de production).",
  },
  D1: {
    code: "D1",
    description:
      "Dépôt sur ou dans le sol (par exemple, mise en décharge, etc …)",
  },
  D2: {
    code: "D2",
    description:
      "Traitement en milieu terrestre (par exemple, biodégradation de déchets liquides ou de boues dans les sols, etc …)",
  },
  D3: {
    code: "D3",
    description:
      "Injection en profondeur (par exemple injection des déchets pompables dans des puits, des dômes de sel ou des failles géologiques naturelles, etc …)",
  },
  D4: {
    code: "D4",
    description:
      "Lagunage (par exemple, déversement de déchets liquides ou de boues dans des puits, des étangs ou des bassins, etc …)",
  },
  D5: {
    code: "D5",
    description:
      "Mise en décharge spécialement aménagée (par exemple, placement dans des alvéoles étanches séparées, recouvertes et isolées les unes et les autres et de l'environnement, etc …)",
  },
  D6: {
    code: "D6",
    description: "Rejet dans le milieu aquatique sauf l'immersion",
  },
  D7: {
    code: "D7",
    description: "Immersion, y compris enfouissement dans le sous-sol marin",
  },
  D8: {
    code: "D8",
    description:
      "Traitement biologique non spécifié ailleurs dans la présente liste, aboutissant à des composés ou à des mélanges qui sont éliminés selon l'un des procédés numérotés D1 à D12",
  },
  D9: {
    code: "D9",
    description:
      "Traitement physico-chimique non spécifié ailleurs dans la présente liste, aboutissant à des composés ou à des mélanges qui sont éliminés selon l'un des procédés numérotés D1 à D12 (par exemple, évaporation, séchage, calcination, etc …)",
  },
  D9F: {
    code: "D9F",
    description:
      "Traitement physico-chimique non spécifié ailleurs dans la présente liste, aboutissant à des composés ou à des mélanges qui sont éliminés selon l'un des procédés numérotés D1 à D12 (par exemple, évaporation, séchage, calcination, etc …)",
  },
  D10: {
    code: "D10",
    description: "Incinération à terre",
  },
  D12: {
    code: "D12",
    description:
      "Stockage permanent (par exemple, placement de conteneurs dans une mine, etc ...)",
  },
  D13: {
    code: "D13",
    description:
      "Regroupement préalablement à l'une des opérations numérotées D1 à D12",
  },
  D14: {
    code: "D14",
    description:
      "Reconditionnement préalablement à l'une des opérations numérotées D1 à D13",
  },
  D15: {
    code: "D15",
    description:
      "Stockage préalablement à l'une des opérations D1 à D14 (à l'exclusion du stockage temporaire, avant collecte, sur le site de production).",
  },
};
