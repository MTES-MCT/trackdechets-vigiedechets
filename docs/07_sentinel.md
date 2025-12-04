# Documentation Module Sentinel (complétée)

## Vue d'ensemble

Le module **Sentinel** (Sentinelle) est une application Django dédiée à la surveillance et l'analyse de la production de déchets .
Il permet d'identifier les entreprises potentiellement non conformes en matière de traçabilité des déchets.

## Objectifs principaux

1. **Surveillance sectorielle** : Analyser la production de déchets par code NAF (nomenclature d'activités française) et par département
2. **Détection d'anomalies** : Identifier les entreprises avec des profils de production de déchets inhabituels
3. **Aide à la décision** : Fournir aux autorités des données pour cibler les contrôles et actions de sensibilisation

## Fonctionnalités

### 1. Recherche par secteur et territoire
- Sélection d'un code NAF (activité économique)
- Choix d'un département
- Visualisation des statistiques nationales et départementales

### 2. Classification des entreprises

Le système catégorise les entreprises en trois groupes :

- **Non inscrites** (`NON_REGISTERED`) : Entreprises du secteur sans compte sur la plateforme de traçabilité
- **Sans activité** (`NO_ACTIVITY`) : Entreprises inscrites mais n'ayant déclaré aucun déchet
- **Profils anormaux** (`ABNORMAL`) : Entreprises avec des proportions de déchets atypiques par rapport à leur secteur

### 3. Analyses statistiques

#### Vue nationale
- Répartition des types de déchets produits par secteur d'activité
- Top 5 des déchets les plus produits
- Quantités totales en tonnes

#### Vue départementale
- Comparaison avec les moyennes nationales du secteur
- Taux d'inscription des entreprises
- Taux d'activité déclarée
- Graphiques de répartition des déchets

### 4. Visualisations
- Graphiques interactifs (Plotly) des répartitions de déchets
- Comparaisons national/départemental
- Indicateurs de performance par territoire

### 5. Export de données
- Génération de fichiers Excel pour chaque catégorie d'entreprises
- Listes détaillées avec adresses et scores d'anomalie
- Format prêt pour exploitation terrain

## Architecture technique

### Modèles de données

**NafCode** : Arborescence hiérarchique des codes NAF
- Structure en arbre (MPTT - Modified Preorder Tree Traversal)
- Recherche full-text avec support des accents
- Organisation par niveaux (section → division → groupe → classe)

### API et endpoints

- **API de recherche NAF** : Autocomplétion et recherche de codes d'activité
- **Vues HTMX** : Chargement dynamique des résultats sans rechargement de page
- **Export XLS** : Génération à la demande de fichiers Excel

### Sources de données

Le module interroge des tables analytiques dans la zone raffinée de l'entrepôt de données :
- Production de déchets par code APE (NAF)
- Production par code APE et département
- Entreprises sans compte
- Entreprises sans activité
- Scores d'anomalie des entreprises

### Sécurité et accès

- **Authentification requise** : Utilisateurs vérifiés uniquement
- **Liste blanche** : Configuration d'emails autorisés via `ALLOWED_USER_FOR_SENTINEL` (temporaire pendant qu'appli en beta)
- **Accès staff** : Personnel administratif avec droits étendus

### Performance

- **Mise en cache** : Top 5 des déchets par secteur (5 minutes)
- **Pagination** : Affichage par pages de 50 résultats
- **Requêtes optimisées** : Agrégations pré-calculées dans l'entrepôt de données

## Architecture Frontend

### Approche progressive sans SPA

Le frontend utilise une approche moderne sans framework JavaScript lourd, basée sur le chargement progressif de contenu.

### HTMX - Interactivité sans JavaScript

**HTMX** permet le chargement dynamique de contenu sans écrire de JavaScript :

- **Chargement progressif** : Les statistiques nationales, départementales et les onglets se chargent séquentiellement
- **Navigation par onglets** : Changement de catégorie (non inscrits, sans activité, anormaux) sans rechargement de page
- **Pagination** : Navigation entre les pages de résultats en AJAX
- **Indicateurs de chargement** : Spinners automatiques pendant les requêtes (`hx-indicator`)

 
### Web Component - Recherche NAF

Un **Web Component personnalisé** (`<naf-search-component>`) gère la recherche de codes NAF :

**Caractéristiques principales :**
- **Shadow DOM** : Encapsulation des styles et du comportement
- **API REST** : Appels asynchrones à l'endpoint de recherche
- **Recherche intelligente** : 
  - Debouncing (500ms) pour limiter les requêtes
  - Affichage hiérarchique des codes NAF
  - Sélection limitée aux codes "feuilles" (codes finaux uniquement)
- **Communication** : Événement personnalisé `selection-changed` pour mettre à jour le formulaire parent
- **UI/UX** :
  - Bouton de réinitialisation
  - États de chargement
  - Messages d'erreur
  - Mise en évidence de la sélection

 
 ### Préparation des données

La commande 
```
    $ manage.py load_nafs
```

permet de charger les codes anfs en db dans une arbOrescence mptt