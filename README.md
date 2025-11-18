# Trackdéchets - Vigiedéchets

## Utilitaire de préparation de fiches d'inspection, téléchargement de registre, contrôle routier et visualisation cartographique

Dépôt de code du projet **Trackdéchets Vigiedéchets** incubé à la Fabrique Numérique du Ministère de la
Transition Écologique.

## Prérequis:

- Une instance de prosgresql récente avec l'extension postgis installée
- Une instance redis
- Le package manager UV https://docs.astral.sh/uv/
- les librairies nécessaires aux fonctionalités géographiques de django (GDAL et GEOS)
- la librairie pango
- [uv](https://docs.astral.sh/uv/) (package manager)

## Installation



### Initialisation d'un environnement Installation des dépendances

```
$ uv sync --frozen
```

Pour installer les dépendances de dev

```
$ uv sync --frozen --group dev
```

Pour installer les dépendances de test

```
$ uv sync --frozen --group test
```

### Variable d'environnement

2 db sont nécessaires:

- DATABASE_URL, managée par django, pour les comptes, les données calculées etc.
- WAREHOUSE_URL, en lecture seule, contenant un dump des données du data warehouse Trackdéchets

Se référer au fichier env.dist

#### Problèmes sur MacOs

Sur macOs, si vous rencontrez une erreur semblable à:

```
    OSError: cannot load library 'libgobject-2.0-0'
```

il peut être nécessaire d'ajouter la variable d'environnement suivante nécessaire au moteur pdf (weasyprint):

```
    $ export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib

```


### Setup de la db

Lancer la commande de migration:

```
    $ uv run python src/manage.py migrate
```

Créer un super utilisateur

```
    $ uv run python src/manage.py createsuperuser
```

### Lancement de l'application

```
    $ uv run python src/manage.py runserver
```

Pour les tâches asynchrones, dans une autre fenêtre de terminal:

```
 
    $ DJANGO_SETTINGS_MODULE='config.settings.dev' uv run celery -A config worker -l info --pool threads
 
```

**NB: l'oubli de `--pool threads` peut conduire à un blocage des tâches asynchrones.**

### Installation des dépendances front

A la racine du projet :

```
    $ npm install
```

### Lancement de l'UI de cartographie

Dans un second terminal,

```
    $ npm run dev
```

### Utilitaires

Pour lancer un rendu de manière synchrone (et glisser plus facilement des breakspoints):

```
    $ uv run python src/manage.py prepare_sheet <sheet_pk>
```

Pour récupérer les établissements depuis le data warehouse:

```
    $ uv run python src/manage.py retrieve_companies
```

### Tests

Cf. config/settings/tests.py

Créer :

- un rôle postgre `inspection`
- une db postgre `inspection_test`

Lancer les tests avec :

```
    $ uv run pytest src
```

### Création en masse d'utilisateurs

Un template xls est disponible à la racine.
Un fois rempli le fichier est importable par la section users de l'interface d'admin (via django-import-export).

### Profiling des workers celery

`py-spy` peut être utilisé pour faire un profiling des tâches celery et créer un _flame graph_. Pour cela il faut dans
un premier temps lancer un _worker celery_ comme expliqué dans la
partie [Lancement de l'application](#lancement-de-lapplication).
Ensuite il faut récupérer le PID du _worker_ :

```sh
ps | grep celery
```

Il va y avoir deux résultats, le bon PID est souvent le second listé.

Ensuite il suffit de lancer `py-spy` en lui passant en paramètre le PID précédent :

```bash
sudo py-spy record -o profile.svg --pid $PID_CELERY --rate 100
```

le paramètre `-o` permet de donner le répertoire de sortie de l'image de profiling. Le paramètre `--rate` permet quant à
lui de régler la fréquence d'échantillonage (ici à 100ms) pour affiner la mesure.

`py-spy` ouvre automatiquement un navigateur permettant d'inspecter de manière interractive le _flame graph_ créé.

### Linting (python + templates)

Utiliser :

```
    $ ./lint.sh
```

Linter de scanning de sécurité

```
    $ bandit -c pyproject.toml -r
```

## Mettre à jour les données des cartes

### En local

```
    $ uv run python srcsrc/manage.py build_stats
    $ ./src/manage.py retrieve_company
```

### En production

Créer un conteneur one-off avec la CLI Scalingo sur l'application trackdechets-preparation-inspection

Carto des ICPE

```
    $ scalingo --app trackdechets-preparation-inspection run bash -c 'pipenv install && pipenv shell && ./src/manage.py build_stats -- settings=config.settings.production'
```

Pour la carto des fiches etablissements

```
    $ scalingo --app trackdechets-preparation-inspection run bash -c 'pipenv install && pipenv shell && ./src/manage.py retrieve_company -- settings=config.settings.production'
```

## Démarrage avec Docker

```bash

cp .env.docker.dist .env.docker

# Lancer tous les services
docker-compose up

```

### Accès aux applications

- Frontend (Vite) : http://localhost:5173
- Backend (Django) : http://localhost:8000

Pour arrêter : `docker-compose down`

### Credentials

admin@test.fr / pass

### Déploiement

Au 10/04/2025 il a été nécessaire d'augmenter la taille du build scalingo de 1.5 à 2 gb.

## Licence

Le code source du logiciel est publié sous licence [MIT](https://fr.wikipedia.org/wiki/Licence_MIT).

