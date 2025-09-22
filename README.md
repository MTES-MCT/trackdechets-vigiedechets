# Trackdéchets - Vigiedéchets

## Utilitaire de préparation de fiches d'inspection, téléchargement de registre, contrôle routier et visualisation cartographique

Dépôt de code du projet **Trackdéchets Vigiedéchets** incubé à la Fabrique Numérique du Ministère de la
Transition Écologique.

## Prérequis:

- Une instance de prosgresql récente avec l'extension postgis installée
- Une instance redis
- Python >= 3.11 avec pipenv
- les librairies nécessaires aux fonctionalités géographiques de django (GDAL et GEOS)

## Installation

Initialisation et activation d'un environnement

```
$ pipenv shell
```

### Installation des dépendances

```
$ pipenv install -d
```

### Variable d'environnement

2 db sont nécessaires:

- DATABASE_URL, managée par django, pour les comptes, les données calculées etc.
- WAREHOUSE_URL, en lecture seule, contenant un dump des données du data warehouse Trackdéchets

Se référer au fichier env.dist

### Setup de la db

Lancer la commande de migration:

```
    $ manage.py migrate
```

Créer un super utilisateur

```
    $ manage.py createsuperuser
```

### Lancement de l'application

```
    $ manage.py runserver
```

Pour les tâches asynchrones, dans une autre fenêtre de terminal:

```
    $ DJANGO_SETTINGS_MODULE='config.settings.dev' celery -A config worker -l info
```

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
    $ manage.py prepare_sheet <sheet_pk>
```

Pour récupérer les établissements depuis le data warehouse:

```
    $ manage.py retrieve_companies
```

### Tests

Cf. config/settings/tests.py

Créer :

- un rôle postgre `inspection`
- une db postgre `inspection_test`

Lancer les tests avec :

```
    $ pytest
```

### Création en masse d'utilisateurs

Un template xls est disponible à la racine.
Un fois rempli le fichier est importable par la section users de l'interface d'admin (via django-import-export).

### Profiling des workers celery

`py-spy` peut être utilisé pour faire un profiling des tâches celery et créer un _flame graph_. Pour cela il faut dans un premier temps lancer un _worker celery_ comme expliqué dans la partie [Lancement de l'application](#lancement-de-lapplication).
Ensuite il faut récupérer le PID du _worker_ :

```sh
ps | grep celery
```

Il va y avoir deux résultats, le bon PID est souvent le second listé.

Ensuite il suffit de lancer `py-spy` en lui passant en paramètre le PID précédent :

```bash
sudo py-spy record -o profile.svg --pid $PID_CELERY --rate 100
```

le paramètre `-o` permet de donner le répertoire de sortie de l'image de profiling. Le paramètre `--rate` permet quant à lui de régler la fréquence d'échantillonage (ici à 100ms) pour affiner la mesure.

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

### Déploiement

Au 10/04/2025 il a été nécessaire d'augmenter la taille du build scalingo de 1.5 à 2 gb.

## Licence

Le code source du logiciel est publié sous licence [MIT](https://fr.wikipedia.org/wiki/Licence_MIT).
