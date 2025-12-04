# Choix technologiques

## Vue d'ensemble

**Vigiedéchets** est une application web Django conçue notamment pour la préparation de fiches d'inspection, le téléchargement de registres, le contrôle routier et la visualisation cartographique. L'architecture privilégie la simplicité, la robustesse et les standards web.

---

## Stack technique principale

### Backend

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **Langage** | Python | Performance, écosystème riche, typage moderne |
| **Framework web** | Django | Framework mature, sécurisé, admin intégré |
| **Base de données** | PostgreSQL | Fiabilité, support des données géospatiales |
| **Extension géospatiale** | PostGIS | Requêtes géographiques avancées |
| **Cache & broker** | Redis | Performance, support Celery natif |
| **Tâches asynchrones** | Celery | Traitement différé, génération de documents |
| **API REST** | Django REST Framework | Sérialisation robuste, documentation auto |
| **Génération PDF** | WeasyPrint | Rendu HTML vers PDF, support CSS moderne |
| **Gestionnaire de paquets** | UV | Installation rapide, gestion des dépendances moderne |

### Frontend

| Composant                   | Technologie | Justification                                     |
|-----------------------------|---------|---------------------------------------------------|
| **Moteur de templates**     | Django Templates | Inclus                                            |
  | **Framework CSS**           | DSFR + CSS custom | Conformité État français                          |
| **Interactivité**           | HTMX | Interactions riches sans complexité SPA           |
| **Composants spécifiques**  | Web Components | Réutilisabilité, encapsulation                    |
| **Cartographie**            | React | Écosystème riche pour la visualisation de données |
| **Build tool**              | Vite | Build rapide, hot reload performant               |
| **Gestionnaire de paquets** | pnpm | Standard de l'écosystème JavaScript               |

### Infrastructure & services

| Service | Technologie | Rôle |
|---------|-------------|------|
| **Hébergement** | Scalingo | PaaS français, conformité RGPD |
| **Stockage fichiers** | S3-compatible | Documents, exports, pièces jointes |
| **Envoi emails** | Brevo (Sendinblue) | Transactionnel, templates, délivrabilité |
| **Monitoring utilisateurs** | Matomo | Analytics respectueux de la vie privée |
| **Monitoring erreurs** | Sentry | Traçabilité des bugs, alertes en temps réel |

---

## Architecture Django

### Structure du projet

Le projet suit une architecture modulaire classique Django avec une séparation claire des responsabilités :

```
src/
├── config/                  # Configuration globale
│   ├── settings/           # Settings par environnement
│   │   ├── base.py        # Configuration commune
│   │   ├── dev.py         # Développement local
│   │   ├── production.py  # Production
│   │   ├── tests.py       # Tests automatisés
│   │   └── docker.py      # Conteneurisation
│   ├── celery_app.py      # Configuration Celery
│   ├── urls.py            # Routes principales
│   └── wsgi.py            # Point d'entrée WSGI
│
├── accounts/              # Gestion des utilisateurs
├── sheets/                # Fiches d'inspection
├── maps/                  # Cartographie
├── registry/              # Registres
├── roadcontrol/           # Contrôles routiers
├── sentinel/              # Module sentinelle
├── faq/                   # FAQ
├── common/                # Utilitaires partagés
└── templates/             # Templates globaux
```

### Configuration par environnement

Le projet utilise **django-environ** pour la gestion des variables d'environnement, avec un fichier de settings dédié par environnement :

- **`base.py`** : Configuration commune à tous les environnements
- **`dev.py`** : Debug activé, outils de développement (Django Debug Toolbar, Django Extensions)
- **`production.py`** : Sécurité renforcée, HTTPS obligatoire, Sentry activé
- **`tests.py`** : Configuration optimisée pour les tests (hashers rapides, tâches Celery synchrones)
- **`docker.py`** : Chemins spécifiques pour les conteneurs

### Bases de données

Le projet utilise deux bases de données distinctes :

1. **Base principale** (`DATABASE_URL`) 
   - Gérée par Django (migrations, ORM)
   - Contient : comptes utilisateurs, données calculées, configuration
   - Engine : `django.contrib.gis.db.backends.postgis`

2. **Data Warehouse** (accès via tunnel SSH + ClickHouse)
   - Base en **lecture seule**
   - Contient : données Trackdéchets
   - Accès via SQLAlchemy pour requêtes analytiques

Le routage entre bases est géré par `config/router.py` :
- App `maps` → Data Warehouse (lecture seule)
- Autres apps → Base principale

---

## Applications Django tierces

### Administration & interface

| Package | Usage |
|---------|-------|
| **grappelli** | Interface admin moderne et personnalisable |
| **django-solo** | Configuration singleton (bannières, paramètres globaux) |
| **django-simple-menu** | Navigation dynamique |
| **django-vite** | Intégration Vite.js dans Django |
| **django-template-partials** | Fragments de templates réutilisables |
| **django-htmx** | Intégration HTMX côté serveur |

### Sécurité & authentification

| Package | Usage |
|---------|-------|
| **django-defender** | Protection contre le bruteforce |
| **django-otp** | Authentification à deux facteurs (email) |
| **mozilla-django-oidc** | Authentification OpenID Connect (MonAIOT, ProConnect) |

### Données & API

| Package | Usage |
|---------|-------|
| **djangorestframework** | API REST pour intégrations externes |
| **django-filter** | Filtrage avancé des querysets |
| **django-mptt** | Arbres hiérarchiques (catégories, FAQ) |
| **django-import-export** | Import/export Excel (utilisateurs, données) |

### Contenu & communication

| Package | Usage |
|---------|-------|
| **django-prose-editor** | Éditeur WYSIWYG sécurisé |
| **django-jsonform** | Formulaires JSON dynamiques |
| **django-anymail** | Envoi emails via Brevo |

### Stockage & fichiers

| Package | Usage |
|---------|-------|
| **django-storages[s3]** | Stockage S3 pour fichiers privés |
| **whitenoise** | Service de fichiers statiques optimisé |

---

## Frontend : architecture hybride

Le projet adopte une **approche hybride** adaptée aux besoins de chaque fonctionnalité :

### 1. Pages traditionnelles (majoritaire)

**Technologies** : Django Templates + HTMX + Vanilla JavaScript

**Avantages** :
- Simplicité de développement
- Pas de build JavaScript complexe
- Temps de chargement initial réduit

**Cas d'usage** :
- Formulaires de saisie
- Pages d'administration
- Tableaux de données
- Workflows multi-étapes

**Exemple** : Fiches d'inspection, gestion des utilisateurs, FAQ

### 2. Interface cartographique (module spécifique)

**Technologies** : React + Vite + Bibliothèques cartographiques


**Cas d'usage** :
- Visualisation des établissements
- Cartes interactives ICPE

### 3. Web Components (éléments réutilisables)

**Technologies** : Vanilla JavaScript + Custom Elements API
 
Utilisé pour la recherche de code NAF dans Sentinelle
---

## Traitement asynchrone

### Celery

**Configuration** : Worker avec pool threads (`--pool threads`)

**Cas d'usage** :
- Génération de fiches d'inspection
- Export de données volumineuses (registre v2, zip de bsds,etc)


**Architecture** :
```
Utilisateur → Django → Celery (via Redis) → Worker → Résultat en base
                ↓
           Notification temps réel (HTMX polling)
```

---

## Sécurité

### Authentification

Le projet supporte **trois mécanismes** d'authentification :

1. **Authentification locale** : Email + mot de passe + 2FA (OTP email)
2. **MonAIOT** : OIDC pour inspecteurs
3. **ProConnect** : OIDC pour agents publics (via CURRASSO)

### Protection

- **Bruteforce** : django-defender (3 tentatives max par IP/username)
- **Sessions** : Durée limitée (4h en production), cookies sécurisés
- **CSRF** : Protection native Django activée


---

## Performance & optimisation

### Base de données

- **Connection pooling** : `CONN_HEALTH_CHECKS = True`
- **Indexes** : Sur les champs fréquemment interrogés
- **Select related** : Réduction des requêtes N+1
- **PostGIS** : Requêtes géospatiales optimisées

### Cache

- **Backend** : Redis
- **Usage** : Sessions, Tâches asynchrones, résultats API, données du DWH
- **TTL** : Adapté par type de donnée

### Fichiers statiques

- **Build** : Vite  
- **Service** : WhiteNoise  

---

## Analyses & données

### Bibliothèques scientifiques

| Package | Usage |
|---------|-------|
| **pandas** | Manipulation de données tabulaires |
| **polars** | Traitement de données haute performance |
| **geopandas** | Analyse géospatiale |
| **numpy** | Calculs numériques |
| **plotly** | Visualisations interactives |

 NB: Polars et Pandas coexistent actuellement car Polars ne propose pas encore de lib cartographique.

## Monitoring & observabilité

### Matomo

**Configuration** : Variable `MATOMO_SITE_ID` dans settings
 
### Sentry

**Configuration** : `SENTRY_URL` en production uniquement

 
---

## Schema Fonctionnel

<pre>
                                                                             ┌────────────┐
                                                                             │   DB de    │
┌──────────────┐                                                    ┌────────┤  Service   │
│ Entrepôt de  │                                                    │        │ (Posgres)  │
│   données    ├────────┐                                           │        └────────────┘
│ (Clickhouse) │        │                                           │
│              │        │                                           │
└──────────────┘        │                                           │
                        │                                           │
                   Tunnel SSH                                       │
                        │        ┌─────────────────────────┐        │
                        │        │                         │        │
                        │        │                         │        │
                        └────────┤      Vigiedéchets       │        │
                                 │                         │────────┘
                       ┌────────▶│                         ├────────┐
                       │         │                         │        │
                       │         └─────────────────────────┘        │
┌──────────────┐       │                                            │         ┌─────────────┐
│              │       │                                            │         │    Redis    │
│     Api      ◀───────┘                                            │         │   Cache /   │
│ Trackdéchets │                                                    └─────────┤   Tâches    │
│              │                                                              │ asynchrones │
└──────────────┘                                                              └─────────────┘
</pre>
 