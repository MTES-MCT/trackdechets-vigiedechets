# Documentation de l'application Contrôle Routier

## Vue d'ensemble

L'application **roadcontrol** (contrôle routier) est un module Django conçu pour les autorités de contrôle françaises (
DREAL, ICPE, Gendarmerie, Douanes, etc.) permettant de rechercher et télécharger des bordereaux de suivi de déchets (
BSD) lors de contrôles routiers ou d'inspections.

## Objectifs principaux

1. **Faciliter les contrôles routiers** : Permettre aux agents de terrain de retrouver rapidement les bordereaux
   transportés par un véhicule
2. **Archivage des contrôles** : Générer des dossiers PDF complets avec tous les bordereaux concernés
3. **Recherche ciblée** : Retrouver un bordereau spécifique par son numéro
4. **Traçabilité** : Conserver l'historique des téléchargements par utilisateur

## Fonctionnalités principales

### 1. Contrôle routier (Road Control)

**Recherche par critères :**

- **SIRET** : Numéro d'identification de l'établissement transporteur (14 chiffres)
- **Immatriculation** : Plaque du véhicule contrôlé
- Au moins un des deux critères est obligatoire

**Processus :**

1. L'agent saisit le SIRET et/ou l'immatriculation
2. Le système interroge l'API Trackdéchets via GraphQL (query dédiée avec permission spécifique lié à un compte
   gouvernemental)
3. Affichage des bordereaux correspondants avec pagination (bordereaux en transit uniquement)
4. Possibilité de télécharger :
    - Un bordereau individuel (PDF unique)
    - Un dossier complet (archive ZIP avec tous les bordereaux + sommaire)

### 2. Recherche de bordereau individuel (BSD Search)

**Recherche par identifiant :**

- Permet de retrouver un bordereau spécifique via son identifiant)
- Téléchargement direct du PDF

### 3. Gestion des archives

**Types de téléchargements :**

- **BsdPdf** : Bordereau individuel
- **PdfBundle** : Dossier complet (archive ZIP)

**Traitement asynchrone :**

- Les archives volumineuses sont traitées en tâche de fond (Celery)

## Architecture technique

### Convertisseurs

Le système supporte **6 types de bordereaux** différents :

- **BSDD** : Déchets dangereux
- **BSDASRI** : Déchets d'activités de soins à risques infectieux
- **BSFF** : Fluides frigorigènes
- **BSDA** : Amiante
- **BSVHU** : Véhicules hors d'usage
- **BSPAOH** : Pièces anatomiques d'origine humaine

Chaque type a son propre structure de données dans l'API Trackdéchets. Les convertisseurs normalisent ces données vers
un format unifié (`BsdDisplay`) pour l'affichage.

### Intégration API Trackdéchets

**GraphQL queries :**

- `controlBsds` : Recherche de bordereaux par SIRET/immatriculation/ID
- `formPdf`, `bsdasriPdf`, etc. : Récupération des liens de téléchargement PDF

**Fragments GraphQL :**
Chaque type de bordereau a son fragment dédié pour récupérer uniquement les champs nécessaires.

### Workflow de création d'archive

```
1. Utilisateur sélectionne plusieurs bordereaux
2. Création d'un PdfBundle (état INITIAL)
3. Lancement tâche Celery → état PROCESSING
4. Pour chaque bordereau :
   - Récupération du lien PDF via API
   - Téléchargement du PDF
   - Création d'un BsdPdf
   - Mise à jour progression
5. Génération sommaire PDF
6. Création archive ZIP
7. Upload sur S3
8. État → READY
```

### Permissions

Système de permissions basé sur les catégories d'utilisateurs :

- **PERMS_ROAD_CONTROL** : Contrôle routier complet
- **PERMS_BSD_SEARCH** : Recherche de bordereaux individuels

## Génération de PDF

**Sommaire du dossier :**

- Utilise WeasyPrint pour la génération
- Template Django → HTML → PDF
- Contient : informations du contrôle, liste des bordereaux, statistiques
- Le rendu des bsdss est effectué par l'api TD

## Points d'attention

### Validation du SIRET

- Vérification en base de données (Warehouse) que l'établissement est inscrit sur Trackdéchets
- Peut être désactivée via `SKIP_ROAD_CONTROL_SIRET_CHECK` (utile en développement)

### Normalisation des données

- Plaques d'immatriculation : suppression des tirets, normalisation des espaces
- SIRET : suppression de tous les espaces

### Pagination

- L'API Trackdéchets utilise une pagination par curseur
- Gestion des curseurs `start_cursor` et `end_cursor`
- Navigation page suivante/précédente

### Stockage

- PDFs stockés sur S3 (storage privé)
- Suppression automatique des fichiers à la suppression du modèle (signal `pre_delete`)

## Points particulier

### Contrôle sans résultat

- Si aucun bordereau trouvé, possibilité de générer un PDF vierge pour le rapport
- Contient les informations du contrôle effectué

### Suivi administratif

- Historique conservé dans "Téléchargements récents"
