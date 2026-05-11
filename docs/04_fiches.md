# Documentation du Module Sheets

## Vue d'ensemble

Le module **sheets** est responsable de la génération de fiches d'inspection établissement .
Il extrait, traite et présente les données de traçabilité depuis le DWH Trackdéchets sous forme de fiches détaillées (
HTML et PDF).

Le suivi des fiches est accesible dans l'admin. Une commande de management nettoie les fiches via un cron (vide les
données sans supprimer les fiches pour conserver une trace)'

## Architecture Générale

```
┌─────────────────┐
│   Utilisateur   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     Interface Web (Views)           │
│  - Formulaire de création           │
│  - Visualisation HTML               │
│  - Téléchargement PDF               │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Traitement Asynchrone (Celery)    │
│  - prepare_sheet                    │
│  - render_pdf                       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│    SheetProcessor                   │
│  1. Extraction des données          │
│  2. Traitement et calculs           │
│  3. Génération des composants       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Stockage (ComputedInspectionData) │
│  - Statistiques (JSON)              │
│  - Graphiques (base64)              │
│  - PDF (base64)                     │
└─────────────────────────────────────┘
```

## Composants Principaux

### 1. Modèle de Données (`models.py`)

**ComputedInspectionData** : Entité centrale stockant toutes les données d'une fiche d'inspection.

**Champs principaux :**

- Identifiants : `org_id` (SIRET), dates de période
- Informations entreprise : nom, adresse, profils
- Données par type de bordereau : BSDD, BSDA, BSDASRI, BSFF, BSVHU
- Données de registres : déchets non dangereux, terres excavées, SSD
- Graphiques pré-calculés (format JSON puis base64 PNG)
- État du traitement : `INITIAL` → `COMPUTED` → `GRAPH_RENDERED`

Le rendu pdf est optionel

**États du cycle de vie :**

```
INITIAL → COMPUTED → GRAPH_RENDERED → (PDF généré)
              ↓
        COMPUTED_FAILED
```

### 2. Extraction de Données (`data_extraction.py`)

**Connexion :**

- Utilise SQLAlchemy + Polars pour requêter un data warehouse ClickHouse
- Connexion via tunnel SSH (`ssh.py`, `datawarehouse.py`)

### 3. Traitement des Données (`data_processing.py`)

**Classe SheetProcessor :**

**Phase 1 : Extraction (méthode `_extract_data()`)**

- Exécution parallèle (ThreadPoolExecutor) de 5 tâches :
    - Données entreprise
    - Bordereaux Trackdéchets
    - Données ICPE
    - Registres
    - Données GISTRID (exports/imports transfrontaliers)

**Phase 2 : Traitement (méthode `_build_components()`)**

- Construction de ~40 composants graphiques et tableaux
- Calculs statistiques (quantités, durées, ratios)
- Génération de visualisations Plotly serilisées et stockées dans le modèle django

### 4. Générateurs de Composants

#### A. Graphiques Plotly (`graph_processors/plotly_components_processors.py`)

**Classes principales :**

- `BsdQuantitiesGraph` : Évolution mensuelle des quantités entrantes/sortantes
- `BsdTrackedAndRevisedProcessor` : Bordereaux émis/reçus/révisés
- `WasteOriginProcessor` : Origine géographique des déchets par type de bordereau (TOP 10 départements)
- `ICPEDailyItemProcessor` / `ICPEAnnualItemProcessor` : Suivi ICPE
- `RegistryQuantitiesGraphProcessor` : Quantités registres DND

#### B. Composants HTML (`graph_processors/html_components_processors.py`)

**Classes principales :**

- `BsdStatsProcessor` : Statistiques agrégées par type de bordereau
- `WasteFlowsTableProcessor` : Tableau exhaustif des flux par code déchet
- `BsdCanceledTableProcessor` / `BsdRefusedTableProcessor` : Anomalies
- `StorageStatsProcessor` : Stock théorique sur site
- `WasteProcessingWithoutICPERubriqueProcessor` : Détection traitement sans autorisation
- `ReceiptAgrementsProcessor` : Récépissés et agréments

**Données retournées :**

- Dictionnaires Python ou listes de dictionnaires
- Sérialisables en JSON
- Consommés par les templates Django

### 5. Rendu PDF (`rendering_helpers.py`, `pdf_processing.py`)

**Pipeline de génération PDF :**

1. **Rendu des graphiques individuels** (parallèle via Celery)

Les graphiques sont converti de Plotly → PNG → base64

2. **Conversion PDF**

On utilise weasyprint et des tempaltes django assortis d'une feuille css dédiée

3. **Stockage**
    - PDF encodé en base64
    - Sauvegardé dans `ComputedInspectionData.pdf`

**Particularité :** Les graphiques sont pré-rendus en PNG et stockés en base64 pour être injectés dans les teampltes
weasyprint.

### 6. Tâches Asynchrones (`task.py`)

**Tâches Celery :**

- **`prepare_sheet()`** : Traitement principal
- **`render_indiv_graph()`** : Rendu intérmediaires
- **`render_pdf()`** : Génération PDF

## Maintenance

### Commandes Management

```bash
 

# Générer une fiche (sync) pour débug
python manage.py prepare_sheet <uuid>

# Nettoyer les anciennes fiches
# Les fiches établissement consomment beaucoup d'espace db. La commande `manage.py void_sheets` vide le contenu des fiches
# de plus de 90jours tout en conservant l'historique.

python manage.py void_sheets
```

### Monitoring

- Durées enregistrées et state de la fiche, auteur, type d'utilisateur (humain ou api)

## Api entrante

La génération de fiche est possible depuis l'ui de Trackdéchets qui fait des appels d'api (cf. module api).
En dehors de l'authentification, le principe est le même que pour la génraiton de fiche par les utilisateurs VD
 