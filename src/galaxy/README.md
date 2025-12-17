# Module Galaxy

Module de visualisation des relations entre établissements sous forme de graphe interactif.

## Vue d'ensemble

Le module Galaxy permet de visualiser les réseaux de collaboration dans la chaîne de gestion des déchets en représentant :
- **Nœuds** : chaque établissement (identifié par SIRET)
- **Liens** : connexions entre établissements lorsqu'ils apparaissent ensemble sur un même bordereau de suivi des déchets (BSD)

## Installation et configuration

### Prérequis

- Python 3.11+
- Node.js et pnpm
- Accès à la base de données ClickHouse (via SSH tunnel)
- Accès à l'application Django avec authentification

### Installation des dépendances

#### Backend (Python)

Les dépendances backend sont déjà incluses dans `pyproject.toml` :
- `polars` : pour le traitement des données
- `sqlalchemy` et `clickhouse-sqlalchemy` : pour la connexion ClickHouse

Aucune installation supplémentaire n'est nécessaire si les dépendances du projet sont déjà installées.

#### Frontend (JavaScript/TypeScript)

Installer la nouvelle dépendance React Flow :

```bash
pnpm install
```

Cela installera `reactflow` (déjà ajouté dans `package.json`).

### Configuration Django

Le module est déjà configuré dans :
- `src/config/settings/base.py` : `"galaxy"` dans `INSTALLED_APPS`
- `src/config/urls.py` : route `/galaxy/` incluse

Aucune configuration supplémentaire n'est nécessaire.

## Exécution en local

### 1. Démarrer le serveur Django

```bash
# Depuis la racine du projet
uv run python src/manage.py runserver
```

Le serveur Django sera accessible sur `http://localhost:8000` (ou le port configuré).

### 2. Builder le frontend React

#### Mode développement (avec hot reload)

```bash
# Depuis la racine du projet
pnpm dev
```

Le serveur Vite sera accessible sur `http://localhost:5173` (ou le port configuré par Vite).

#### Mode production (build)

```bash
# Depuis la racine du projet
pnpm build
```

Cela générera les fichiers compilés dans `src/static/ui_app_ts/dist/`.

**Note** : En développement, `django-vite` utilise le serveur Vite en mode HMR (Hot Module Replacement). En production, il utilise les fichiers compilés.

### 3. Accéder au module

1. Se connecter à l'application Django avec un compte autorisé
2. Accéder à l'URL : `http://localhost:8000/galaxy/`

### 4. Permissions

Le module utilise les mêmes permissions que le module `maps` (`PERMS_MAP`). Les utilisateurs autorisés incluent :
- Staff Trackdéchets
- Administration centrale
- Inspecteurs ICPE
- CTT
- Inspection du travail
- Gendarmerie
- ARS
- Douane
- Observatoire

## Utilisation

### Interface

L'interface affiche un graphe interactif avec :
- **Nœuds** : établissements (SIRET)
- **Liens** : relations entre établissements (épaisseur = nombre de BSD en commun)
- **Contrôles** : zoom, pan, minimap

### API

L'endpoint API est accessible à : `/galaxy/api/graph`

#### Paramètres de requête

- `siret` (optionnel) : Filtrer autour d'un établissement spécifique
- `bsd_types` (optionnel) : Liste des types de BSD (actuellement seul `bsdd` est supporté)
- `date_from` (optionnel) : Date de début (format YYYY-MM-DD)
- `date_to` (optionnel) : Date de fin (format YYYY-MM-DD)
- `min_weight` (optionnel, défaut: 1) : Nombre minimum de BSD en commun pour afficher un lien

#### Exemple de requête

```bash
curl -X GET "http://localhost:8000/galaxy/api/graph?siret=12345678901234&min_weight=5" \
  -H "Cookie: sessionid=..."
```

## Structure du code

### Backend

```
src/galaxy/
├── __init__.py
├── apps.py              # Configuration Django app
├── services.py          # Service métier pour construire le graphe
├── api.py               # Endpoint API REST
├── serializers.py       # Sérializers DRF
├── views.py             # Vue Django
└── urls.py              # Routes
```

### Frontend

```
src/static/ui_app_ts/src/
├── galaxy.tsx                    # Point d'entrée React
├── components/galaxy/
│   ├── GalaxyApp.tsx            # Composant principal
│   └── Graph.tsx                # Composant de visualisation React Flow
└── store/
    └── galaxySlice.ts           # Redux slice pour la gestion d'état
```

## Développement

### Modifier le service backend

Le service `GalaxyGraphService` dans `src/galaxy/services.py` peut être étendu pour :
- Ajouter d'autres types de BSD (BSDA, BSFF, etc.)
- Améliorer les filtres
- Calculer des métriques avancées (centralité, etc.)

### Modifier le frontend

Les composants React sont dans `src/static/ui_app_ts/src/components/galaxy/`.

Pour ajouter des fonctionnalités :
1. Modifier les composants React
2. Le hot reload de Vite rechargera automatiquement les changements

### Tests

Pour tester le module :

1. **Backend** : Vérifier que l'API retourne des données
   ```bash
   # Se connecter à l'application, puis tester l'API
   curl http://localhost:8000/galaxy/api/graph
   ```

2. **Frontend** : Vérifier que le graphe s'affiche correctement
   - Accéder à `http://localhost:8000/galaxy/`
   - Vérifier que les nœuds et liens s'affichent
   - Tester les interactions (zoom, pan)

## Limitations actuelles

- **Types de BSD** : Seul BSDD est supporté actuellement
- **Relations** : Seules les relations emitter-destination sont affichées
- **Performance** : Limité à 1000 relations par requête
- **Sécurité SQL** : Les paramètres de requête utilisent une validation basique (à améliorer en production)

## Améliorations futures

- [ ] Support de tous les types de BSD (BSDA, BSFF, BSDASRI, BSVHU, etc.)
- [ ] Support des relations multiples (emitter, transporter, destination, worker)
- [ ] Filtres interactifs dans l'UI
- [ ] Panneau de détails pour les nœuds sélectionnés
- [ ] Layout algorithm amélioré (force-directed avec paramètres)
- [ ] Cache Redis pour les graphes pré-calculés
- [ ] Export du graphe (PNG, SVG, JSON)
- [ ] Amélioration de la sécurité SQL avec paramètres SQLAlchemy

## Dépannage

### Le graphe ne s'affiche pas

1. Vérifier que le frontend est compilé : `pnpm build` ou `pnpm dev`
2. Vérifier la console du navigateur pour les erreurs JavaScript
3. Vérifier que l'API retourne des données : tester `/galaxy/api/graph`

### Erreur de connexion ClickHouse

1. Vérifier que le tunnel SSH est actif
2. Vérifier les variables d'environnement `DWH_*` dans `.env`
3. Vérifier les logs Django pour plus de détails

### Erreur de permissions

1. Vérifier que l'utilisateur est authentifié
2. Vérifier que l'utilisateur a les permissions `PERMS_MAP`
3. Vérifier les logs Django pour les erreurs d'authentification

## Support

Pour toute question ou problème, consulter :
- L'analyse d'impact : `.cursor/impact_analysis/IMPACT_ANALYSIS_GALAXY_MODULE.md`
- La documentation du projet : `docs/`
- Le code source du module `maps` pour des exemples similaires
