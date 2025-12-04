# Installation

NB: Vigiedéchets a changé de noms à plusieurs reprise, i est possible de trouver des référence à:

- fiche d'inspection
- fiche établissement
- gerico (notamment dans l'api TD)
-

## Prérequis système

Avant de commencer l'installation, assurez-vous d'avoir les éléments suivants :

### Base de données et cache

- **PostgreSQL** (version 12 ou supérieure) avec l'extension **PostGIS** installée
- **Redis** (version 5 ou supérieure)

### Gestionnaire de paquets

- **uv** - Gestionnaire de paquets Python moderne ([documentation](https://docs.astral.sh/uv/))
- **pnpm** - Pour les dépendances frontend

### Bibliothèques système

- **GDAL** - Bibliothèque de traduction de données géospatiales
- **GEOS** - Moteur de géométrie
- **Pango** - Bibliothèque nécessaire pour le rnedu pdf

#### Installation des bibliothèques sur Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib postgis redis-server
sudo apt-get install gdal-bin libgdal-dev libgeos-dev libpango1.0-dev
```

#### Installation des bibliothèques sur macOS

```bash
brew install redis gdal geos pango
```

### Stockage de fichiers

- Un service compatible **S3** (AWS S3, Scaleway Object Storage, Minio, etc.)

---

## Installation du projet

### 1. Cloner le dépôt

```bash
git clone <url-du-depot>
cd trackdechets-vigiedechets
```

### 2. Installer les dépendances Python

#### Installation des dépendances de base

```bash
uv sync --frozen
```

#### Installation des dépendances de développement

```bash
uv sync --frozen --group dev
```

#### Installation des dépendances de test

```bash
uv sync --frozen --group test
```

### 3. Configuration des variables d'environnement

Copiez le fichier d'exemple et configurez vos variables :

```bash
cp .env.dist .env
```

Éditez le fichier `.env` et configurez les variables suivantes :

#### Variables essentielles

```bash
# Django
DEBUG=True
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire
ALLOWED_HOST=localhost,127.0.0.1
BASE_URL=http://127.0.0.1:8000

# Base de données principale (Django)
DATABASE_URL=postgis://utilisateur:motdepasse@localhost:5432/vigiedechets

# Redis
REDIS_URL=redis://localhost:6379/0

# Accès au Data Warehouse (via tunnel SSH)
DWH_USERNAME=votre-username
DWH_PASSWORD=votre-password
DWH_PORT=8123
DWH_SSH_HOST=host-distant
DWH_SSH_PORT=22
DWH_SSH_USERNAME=votre-ssh-username
DWH_SSH_LOCAL_BIND_HOST=127.0.0.1
DWH_SSH_KEY="-----BEGIN OPENSSH PRIVATE KEY-----
votre-cle-ssh-privee
-----END OPENSSH PRIVATE KEY-----"
DWH_SSH_KEY_PASSPHRASE=passphrase-si-necessaire

# Stockage S3
AWS_S3_ENDPOINT_URL=https://s3.fr-par.scw.cloud
AWS_S3_BUCKET_NAME=votre-bucket
AWS_S3_ACCESS_KEY_ID=votre-access-key
AWS_S3_SECRET_ACCESS_KEY=votre-secret-key
AWS_S3_REGION_NAME=fr-par
PARQUET_BUCKET_NAME=votre-bucket-parquet

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# Admin et API
ADMIN_SLUG=admin
API_SLUG=api

# OpenID Connect (optionnel en dev)
MONAIOT_OIDC_RP_CLIENT_SECRET=secret
MONAIOT_OIDC_OP_SERVER_URL=https://auth.server.url
PROCONNECT_OIDC_RP_CLIENT_ID=client-id
PROCONNECT_OIDC_RP_CLIENT_SECRET=secret
PROCONNECT_OIDC_OP_SERVER_URL=https://auth.proconnect.url

# Dates de mise à jour des données
GUN_DATA_UPDATE_DATE_STRING=2025-01-01
GISTRID_DATA_UPDATE_DATE_STRING=2025-01-01
RNDTS_DATA_UPDATE_DATE_STRING=2025-01-01

# Support
SUPPORT_FORM_RECIPIENT=support@example.com
MESSAGE_RECIPIENTS=admin@example.com
```

### 4. Configuration de la base de données

#### Créer la base de données PostgreSQL

```bash
# Se connecter à PostgreSQL
# Créer la base de données
CREATE DATABASE vigiedechets;

# Créer un utilisateur (si nécessaire)
CREATE USER vigiedechets_user WITH PASSWORD 'votre_mot_de_passe';

# Activer l'extension PostGIS
\c vigiedechets
CREATE EXTENSION IF NOT EXISTS postgis;

# Quitter
\q
```

#### Appliquer les migrations

```bash
uv run python src/manage.py migrate
```

#### Créer un super utilisateur

```bash
uv run python src/manage.py createsuperuser
```

Suivez les instructions pour définir l'email et le mot de passe.

### 5. Chargement des données initiales

Charger les codes NAF pour le module Sentinelle (à faire une seule fois) :

```bash
uv run python src/manage.py load_nafs
```

### 6. Installation des dépendances frontend

À la racine du projet :

```bash
npm install
# ou avec pnpm
pnpm install --frozen-lockfile
```

---

## Lancement de l'application

### 1. Démarrer le serveur de développement Django

Dans un premier terminal :

```bash
uv run python src/manage.py runserver
```

L'application sera accessible à l'adresse : **http://127.0.0.1:8000**

### 2. Démarrer le worker Celery (tâches asynchrones)

Dans un deuxième terminal :

```bash
DJANGO_SETTINGS_MODULE='config.settings.dev' uv run celery -A config worker -l info --pool threads
```

⚠️ **Important** : L'option `--pool threads` est obligatoire pour éviter le blocage des tâches asynchrones.

### 3. Démarrer le serveur de développement frontend

Dans un troisième terminal :

```bash
npm run dev
# ou avec pnpm
pnpm run dev
```

L'interface de cartographie sera disponible sur le port configuré par Vite (généralement http://localhost:5173).

---

## Problèmes connus

### Erreur sur macOS : `cannot load library 'libgobject-2.0-0'`

Si vous rencontrez cette erreur liée au moteur PDF WeasyPrint, ajoutez la variable d'environnement suivante :

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
```

Vous pouvez l'ajouter dans votre fichier `~/.zshrc` ou `~/.bashrc` pour qu'elle soit persistante.

---

## Commandes utiles

### Gestion des données

```bash
# Récupérer les établissements depuis le data warehouse
uv run python src/manage.py retrieve_companies

# Construire les statistiques pour les cartes
uv run python src/manage.py build_stats

# Préparer une fiche de manière synchrone (utile pour le debug)
uv run python src/manage.py prepare_sheet <sheet_pk>
```

### Tests

```bash
# Lancer tous les tests
uv run pytest src

# Lancer les tests avec couverture
uv run pytest src --cov
```

### Qualité du code

```bash
# Linting Python et templates
./lint.sh

# Analyse de sécurité
bandit -c pyproject.toml -r src
```

---

## Accès à l'application

Une fois l'application lancée :

- **Interface publique** : http://127.0.0.1:8000
- **Interface privée** : http://127.0.0.1:8000/home/
- **Administration Django** : http://127.0.0.1:8000/admin/
- **Cartographie** : http://localhost:5173

### Compte par défaut (Docker uniquement)

- Email : `admin@test.fr`
- Mot de passe : `pass`

 
 
 