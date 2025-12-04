# Documentation du Module Maps

## Vue d'ensemble

Le module `maps` est un système de cartographie et de visualisation des établissements de gestion des déchets en France. Il permet de localiser, filtrer et analyser les établissements en fonction de leurs activités, rôles et types de déchets traités.
C'est le seul module ou on copie des données en masse depuis l'entrepôt pour assurer une fluidité d'affichage acceptable.


## Fonctionnalités principales

### 1. Cartographie des établissements

Le module centralise les informations sur les établissements impliqués dans la gestion des déchets :

- **Localisation géographique** : coordonnées GPS, adresses, codes INSEE (commune, département, région)
- **Identification** : SIRET, raison sociale, date d'inscription sur Trackdéchets
- **Profils** : collecteur, installation de traitement, transporteur, courtier, négociant, éco-organisme, etc.

 
## Architecture des données

### Modèle principal : CartoCompany

Représente un établissement avec :
- Informations d'identification (SIRET, nom, adresse)
- Coordonnées géographiques
- Profils et rôles pour chaque type de BSD
- Codes déchets traités ou émis
- Opérations de traitement réalisées

### Modèles de calculs ICPE

- **InstallationsComputation** : statistiques par installation
- **DepartementsComputation** : agrégation départementale
- **RegionsComputation** : agrégation régionale
- **FranceComputation** : vue nationale

Chaque modèle contient :
- Quantités autorisées et traitées
- Taux de consommation de la capacité
- Graphiques d'évolution temporelle
- Nombre d'installations (pour agrégations)

## API REST

### Endpoints principaux

#### `/map/api/companies/objects`
- Liste les établissements ou clusters selon le niveau de zoom
- Filtres disponibles :
  - Zone géographique (bounds)
  - Départements
  - Types de BSD et rôles
  - Codes déchets
  - Opérations de traitement
  - Profils d'établissements

#### `/map/api/companies/export`
- Export des établissements filtrés
- Formats : CSV ou Excel (XLSX)
- Limite : 1500 établissements maximum

#### `/map/api/icpe/...`
- Données ICPE par rubrique et année
- Niveaux : installations, départements, régions, France
- Graphiques temporels par installation/zone

## Système de filtrage

### Filtres géographiques
- **Bounds** : rectangle de délimitation (bounding box)
- **Départements** : liste de codes départements INSEE
- **Clustering automatique** : agrégation par région ou département selon le niveau de zoom

### Filtres métier
- **bsds_roles** : combinaison type BSD + rôle (ex: "bsdd_emitter,bsda_destination")
- **operation_codes** : codes d'opérations de traitement
- **waste_codes** : codes nomenclature déchets
- **profils** : types d'établissements

### Logique de clustering

Le système adapte le niveau de détail selon la diagonale de la zone visualisée :
-  affichage par région, par département ou affichage des établissements individuels
 

## Processus de calcul ICPE

### Pipeline de traitement

1. **Extraction des données** : requêtes SQL vers l'entrepôt de données (ClickHouse)
2. **Traitement avec Polars** : agrégations et calculs de métriques
3. **Génération de graphiques** : visualisations Plotly en JSON
4. **Stockage en base** : sauvegarde des résultats calculés

### Métriques calculées

- **Quantité autorisée** : capacité maximale de l'installation
- **Quantité traitée** : cumul annuel ou moyenne journalière selon la rubrique
- **Taux de consommation** : ratio quantité traitée / quantité autorisée
- **Seuil TGAP majoré** : seuil de taxe environnementale (depuis 2024)

## Vues et interfaces

### Vue carte principale (`/map/`) et carte ICPE (`/map/exutoires`)
Restreint aux catégories d'utilisateurs définis.
 
 
## Commandes de gestion

### `build_stats`
Construit les statistiques et graphiques ICPE :
1. Nettoie les anciennes données
2. Génère les dataframes Polars
3. Calcule les métriques pour chaque année (2022-2025)
4. Sauvegarde en base de données

### `retrieve_companies`
Import des données d'établissements depuis l'entrepôt :
- Suppression des données existantes
- Import par lots (pagination)
- Dédoublonnage par SIRET
- Nettoyage des valeurs NaN
 