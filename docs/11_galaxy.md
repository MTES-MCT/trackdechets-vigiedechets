# Documentation du Module Galaxy

## Vue d'ensemble

Le module **Galaxy** permet de visualiser les relations entre établissements sous forme de graphe interactif, révélant les réseaux de collaboration dans la chaîne de gestion des déchets. Chaque établissement est représenté par un nœud, et les connexions entre établissements existent lorsqu'ils apparaissent ensemble sur un même bordereau de suivi des déchets (BSD).

Cette fonctionnalité a été développée initialement comme démonstration lors d'un séminaire et a suscité un fort intérêt côté administration. Elle répond à la question : "Qui travaille avec qui et en quelle proportion ?"

## Fonctionnalités principales

### 1. Visualisation de graphe interactif

Le module affiche un graphe où :
- **Nœuds** : chaque établissement est représenté par un nœud identifié par son SIRET
- **Liens** : une connexion entre deux établissements existe lorsqu'ils apparaissent ensemble sur un même BSD
- **Poids des liens** : l'épaisseur du lien indique le nombre de BSD en commun entre deux établissements

### 2. Types de relations

Les liens peuvent représenter différents types de relations selon les rôles sur le bordereau :
- **Producteur ↔ Destinataire** : relation emitter-destination
- **Producteur ↔ Transporteur** : relation emitter-transporter
- **Transporteur ↔ Destinataire** : relation transporter-destination
- **Autres combinaisons** selon les types de BSD (BSDD, BSDA, BSFF, etc.)

### 3. Interactions

- **Zoom et pan** : navigation dans le graphe
- **Sélection de nœuds** : clic sur un établissement pour voir ses détails
- **Minimap** : vue d'ensemble du graphe
- **Contrôles** : reset du zoom, export (à venir)

## Architecture

### Backend Django

Le module suit une architecture similaire au module `maps` :

**Structure** :
```
src/galaxy/
├── apps.py              # Configuration Django app
├── services.py          # Service métier pour construire le graphe
├── api.py               # Endpoint API REST
├── serializers.py       # Sérializers DRF
├── views.py             # Vue Django
└── urls.py              # Routes
```

**Service métier** : `GalaxyGraphService`
- Extrait les relations depuis ClickHouse (`trusted_zone_trackdechets`)
- Agrège les relations par type de BSD
- Calcule les métriques (degré des nœuds, poids des liens)
- Construit les structures nodes/edges pour le frontend

### Frontend React

**Structure** :
```
src/static/ui_app_ts/src/
├── galaxy.tsx                    # Point d'entrée React
├── components/galaxy/
│   ├── GalaxyApp.tsx            # Composant principal
│   └── Graph.tsx                # Composant de visualisation React Flow
└── store/
    └── galaxySlice.ts           # Redux slice pour la gestion d'état
```

**Technologies** :
- **React Flow** : bibliothèque de visualisation de graphes
- **Redux Toolkit** : gestion d'état
- **Axios** : appels API
- **Vite** : build tool (intégré avec django-vite)

## API REST

### Endpoint principal

#### `/galaxy/api/graph`

Retourne les données du graphe au format JSON avec les nœuds et les liens.

**Méthode** : `GET`

**Authentification** : Session (utilisateur authentifié et vérifié)

**Permissions** : `UserIsVerifedPermission` (même que le module maps)

**Paramètres de requête** :

- `siret` (optionnel) : Filtrer autour d'un établissement spécifique
  - Format : 14 chiffres (SIRET)
  - Exemple : `?siret=12345678901234`

- `bsd_types` (optionnel) : Liste des types de BSD à inclure
  - Valeurs possibles : `bsdd`, `bsda`, `bsff`, `bsdasri`, `bsvhu`, etc.
  - Exemple : `?bsd_types=bsdd&bsd_types=bsda`

- `date_from` (optionnel) : Date de début pour filtrer les BSD
  - Format : `YYYY-MM-DD`
  - Exemple : `?date_from=2024-01-01`

- `date_to` (optionnel) : Date de fin pour filtrer les BSD
  - Format : `YYYY-MM-DD`
  - Exemple : `?date_to=2024-12-31`

- `min_weight` (optionnel, défaut: 1) : Nombre minimum de BSD en commun pour afficher un lien
  - Format : entier
  - Exemple : `?min_weight=5`

**Réponse** :

```json
{
  "nodes": [
    {
      "id": "12345678901234",
      "label": "12345678901234",
      "size": 10,
      "type": ["emitter", "destination"],
      "metadata": {}
    }
  ],
  "edges": [
    {
      "source": "12345678901234",
      "target": "98765432109876",
      "weight": 15,
      "types": ["bsdd"],
      "roles": ["emitter->destination"]
    }
  ]
}
```

**Exemple de requête** :

```bash
curl -X GET "http://localhost:8000/galaxy/api/graph?siret=12345678901234&min_weight=5" \
  -H "Cookie: sessionid=..."
```

## Vues et interfaces

### Vue principale : `/galaxy/`

Page principale du module accessible aux utilisateurs autorisés.

**Permissions** : `PERMS_MAP` (même que le module maps)

**Catégories d'utilisateurs autorisées** :
- Staff Trackdéchets
- Administration centrale
- Inspecteurs ICPE
- CTT
- Inspection du travail
- Gendarmerie
- ARS
- Douane
- Observatoire

**Template** : `src/templates/galaxy/galaxy.html`

**Fonctionnalités** :
- Chargement automatique du graphe au chargement de la page
- Affichage du graphe avec React Flow
- Interactions : zoom, pan, sélection
- Gestion des erreurs et états de chargement

## Données sources

### Base de données ClickHouse

Le module interroge directement l'entrepôt de données ClickHouse via les tables :
- `trusted_zone_trackdechets.bsdd` : Bordereaux de suivi des déchets dangereux
- `trusted_zone_trackdechets.bsda` : Bordereaux de suivi des déchets d'amiante (à venir)
- `trusted_zone_trackdechets.bsff` : Bordereaux de suivi des fluides frigorigènes (à venir)
- Etc.

### Champs utilisés

Pour chaque type de BSD, les champs suivants sont extraits :
- `emitter_company_siret` : SIRET de l'émetteur
- `recipient_company_siret` / `destination_company_siret` : SIRET du destinataire
- `transporter_company_siret` : SIRET du transporteur (selon le type de BSD)
- `worker_company_siret` : SIRET de l'entreprise de travaux (pour BSDA)
- `sent_at` : Date d'envoi (pour filtrage temporel)
- `status` : Statut du bordereau (exclut DRAFT, INITIAL)
- `is_deleted` : Indicateur de suppression

## Limitations actuelles

### Types de BSD supportés

**Actuellement implémenté** :
- ✅ BSDD (Bordereau de suivi des déchets dangereux)

**À venir** :
- ⏳ BSDA (Bordereaux de suivi des déchets d'amiante)
- ⏳ BSFF (Bordereaux de suivi des fluides frigorigènes)
- ⏳ BSDASRI (Bordereaux de suivi des déchets d'activités de soins)
- ⏳ BSVHU (Bordereaux de suivi des véhicules hors d'usage)
- ⏳ BSDND (Bordereaux de suivi des déchets non dangereux)

### Relations supportées

**Actuellement implémenté** :
- ✅ Emitter → Destination (Producteur → Destinataire)

**À venir** :
- ⏳ Emitter → Transporter (Producteur → Transporteur)
- ⏳ Transporter → Destination (Transporteur → Destinataire)
- ⏳ Worker (Entreprise de travaux) pour BSDA

### Performance

- **Limite de résultats** : 1000 relations maximum par requête
- **Limite de nœuds** : Pas de limite actuelle (peut impacter les performances avec de très grands graphes)
- **Cache** : Pas de cache implémenté actuellement (chaque requête interroge ClickHouse)

## Développement

### Ajouter un nouveau type de BSD

Pour ajouter le support d'un nouveau type de BSD (ex: BSDA) :

1. **Modifier `services.py`** :
   - Ajouter une requête SQL pour le nouveau type de BSD
   - Adapter les champs selon la structure de la table
   - Gérer les rôles spécifiques (ex: `worker_company_siret` pour BSDA)

2. **Mettre à jour les filtres** :
   - Ajouter le type dans la liste `bsd_types` acceptés
   - Adapter la logique d'agrégation

3. **Tester** :
   - Vérifier que les relations sont correctement extraites
   - Vérifier que les filtres fonctionnent
   - Vérifier les performances avec des données réelles

### Améliorer les performances

Pour améliorer les performances avec de grands graphes :

1. **Limiter le nombre de nœuds** :
   - Filtrer par établissement central (`siret`)
   - Limiter par période (`date_from`, `date_to`)
   - Augmenter `min_weight` pour réduire le nombre de liens

2. **Implémenter un cache** :
   - Utiliser Redis pour stocker les graphes pré-calculés
   - Créer des tâches Celery pour pré-calculer les graphes fréquents
   - Invalider le cache lors de mises à jour des données

3. **Optimiser les requêtes** :
   - Utiliser des index appropriés dans ClickHouse
   - Limiter la période de données par défaut
   - Utiliser des agrégations au niveau ClickHouse

### Personnaliser la visualisation

Pour personnaliser l'apparence du graphe :

1. **Modifier `Graph.tsx`** :
   - Changer les styles des nœuds (couleur, taille, forme)
   - Changer les styles des liens (couleur, épaisseur, style)
   - Ajouter des labels personnalisés

2. **Ajouter des composants personnalisés** :
   - Créer des composants Node et Edge personnalisés
   - Ajouter des panneaux latéraux (détails, filtres, légende)
   - Ajouter des contrôles interactifs

3. **Améliorer le layout** :
   - Utiliser des algorithmes de layout différents (hierarchical, force-directed avec paramètres)
   - Implémenter un layout personnalisé selon les métriques (centralité, etc.)

## Évolutions futures

### Court terme

- [ ] Support de tous les types de BSD
- [ ] Support de toutes les relations (emitter, transporter, destination, worker)
- [ ] Filtres interactifs dans l'UI
- [ ] Panneau de détails pour les nœuds sélectionnés
- [ ] Légende pour les types de relations et BSD

### Moyen terme

- [ ] Analyse de centralité (betweenness, closeness, etc.)
- [ ] Détection de communautés (clusters d'établissements)
- [ ] Export du graphe (PNG, SVG, JSON)
- [ ] Cache Redis pour les graphes pré-calculés
- [ ] Tâches Celery pour pré-calcul

### Long terme

- [ ] Visualisation de l'évolution des relations dans le temps
- [ ] Filtres avancés (par code déchet, opération de traitement, etc.)
- [ ] Comparaison de graphes (avant/après, période 1 vs période 2)
- [ ] Alertes sur les établissements centraux ou les relations suspectes

## Dépannage

### Le graphe ne s'affiche pas

1. **Vérifier le frontend** :
   - Vérifier que `pnpm build` ou `pnpm dev` a été exécuté
   - Vérifier la console du navigateur pour les erreurs JavaScript
   - Vérifier que `reactflow` est installé : `pnpm list reactflow`

2. **Vérifier l'API** :
   - Tester l'endpoint `/galaxy/api/graph` directement
   - Vérifier que l'API retourne des données valides
   - Vérifier les logs Django pour les erreurs

3. **Vérifier les permissions** :
   - Vérifier que l'utilisateur est authentifié
   - Vérifier que l'utilisateur a les permissions `PERMS_MAP`
   - Vérifier les logs Django pour les erreurs d'authentification

### Erreur de connexion ClickHouse

1. **Vérifier le tunnel SSH** :
   - Vérifier que le tunnel SSH est actif
   - Vérifier les variables d'environnement `DWH_*` dans `.env`
   - Vérifier les logs Django pour les erreurs de connexion

2. **Vérifier les requêtes** :
   - Vérifier que les tables existent dans ClickHouse
   - Vérifier que les champs utilisés existent dans les tables
   - Vérifier les logs Django pour les erreurs SQL

### Performance lente

1. **Réduire la taille du graphe** :
   - Utiliser le filtre `siret` pour centrer sur un établissement
   - Utiliser les filtres `date_from` et `date_to` pour limiter la période
   - Augmenter `min_weight` pour réduire le nombre de liens

2. **Vérifier les requêtes** :
   - Vérifier le temps d'exécution des requêtes dans les logs
   - Vérifier que les index sont utilisés dans ClickHouse
   - Considérer l'implémentation d'un cache

## Références

- **Analyse d'impact** : `.cursor/impact_analysis/IMPACT_ANALYSIS_GALAXY_MODULE.md`
- **Ticket Favro** : `.cursor/impact_analysis/GALAXY_MODULE_FAVRO_TICKET.md`
- **README du module** : `src/galaxy/README.md`
- **Documentation React Flow** : https://reactflow.dev/
- **Module maps** (référence) : `docs/09_maps.md`
