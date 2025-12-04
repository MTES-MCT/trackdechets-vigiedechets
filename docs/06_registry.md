# Documentation - Module Registry

## Vue d'ensemble

Le module **Registry** permet aux utilisateurs de générer et télécharger des registres de déchets depuis Trackdéchets.

Les regsitres sont générés sur TD et téléchargés sur Vigiedéchets

## Architecture

### Schéma de fonctionnement

```
Utilisateur → Formulaire → RegistryV2Export (DB)
                                ↓
                         Celery Task (generate)
                                ↓
                         API Trackdéchets
                                ↓
                         Celery Task (refresh)
                                ↓
                         Téléchargement (URL signée)
```

### 2. Traitement asynchrone

Une fois le formulaire validé :

**a) Création de l'export distant** (`generate_registry_export`)

- Appel GraphQL vers l'API Trackdéchets (mutation GenerateRegistryV2Export avec droits gouvernementaix)
- Retry avec délai géométrique en cas d'erreur HTTP

**b) Rafraîchissement du statut** (`refresh_registry_export`)

- Polling régulier de l'API pour vérifier l'état
- Retry toutes les 10 secondes (statique) si en cours
- Mise à jour de l'état en base quand terminé

### 3. Téléchargement

Lorsque l'export est au statut SUCCESSFUL :

- Appel GraphQL pour obtenir une URL signée S3
- Redirection vers l'URL de téléchargement

 