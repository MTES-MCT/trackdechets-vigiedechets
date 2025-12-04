# Documentation Module FAQ

## Vue d'ensemble

Le module **FAQ**   fournit un système   de gestion de documentation d'aide et d'assistance pour les utilisateurs.
Il permet de structurer et d'organiser l'information sous forme de pages hiérarchiques, avec  recherche avancées et un form de contact intégré.

## Fonctionnalités principales

### 1. Pages FAQ

Les pages FAQ constituent le cœur du module et offrent :

- **Organisation hiérarchique** : Les pages sont structurées en arborescence multi-niveaux, permettant une navigation intuitive du général au spécifique
- **Contrôle d'accès par catégorie** : Chaque page peut être restreinte à certaines catégories d'utilisateurs (inspecteurs ICPE, gendarmerie, ARS, douane, etc.) ou être accessible à tous
- **Contenu enrichi** : Chaque page peut contenir plusieurs blocs de contenu avec texte formaté, images et vidéos
- **Pages suggérées** : Système de recommandations pour guider l'utilisateur vers des contenus connexes

### 2. Blocs de contenu

Les blocs de contenu permettent de composer les pages FAQ avec :

- Éditeur de texte riche (gras, italique, titres, listes, liens)
- Support des images hébergées
- Intégration de vidéos YT via URL
- Remplacement automatique de tags spéciaux (ex: `#ASSISTANCE` vers lien FAQ) et nettoyage du balisage superflu de l'editeur
- Organisation par ordre de priorité

### 3. Recherche plein texte

Le système de recherche permet  :

- Recherche dans les titres et contenus des pages
- Recherche sans accent
- Mise en srulignage des résultats
- Classement par pertinence
- Génération automatique d'extraits contextuels
- Respect des restrictions d'accès par catégorie d'utilisateur

### 4. Pages d'assistance

Complément aux pages FAQ, les pages d'assistance offrent  (idem assiatnce TD):

- Structure arborescente similaire aux pages FAQ
- Titres de navigation personnalisables
- Formulaires de contact intégrés (ouverts, fermés ou absents)
- Gestion de l'affichage conditionnel des formulaires

### 5. Système de contact

Le formulaire de contact permet aux utilisateurs de :

- Envoyer des demandes d'assistance avec sujet et message
- Joindre jusqu'à 5 fichiers (PDF, images, documents Office)
- Identifier automatiquement la page d'origine
- Archiver les messages avec métadonnées (IP, utilisateur, date)

Les messages sont envoyés par email à l'équipe support et enregistrés en base de données.

### 6. Gestion des webinaires

Module complémentaire pour les événements de formation :

- Planification des webinaires avec date, heure et durée
- Liens visioconférence
- Affichage conditionnel (X jours avant l'événement)
- Export au format iCalendar (.ics) pour ajout au calendrier
- Filtrage automatique (webinaires futurs/passés/visibles)
- Affichage sur la page de bienvenue unqiuement

## Architecture technique

### Modèles de données

Le module utilise **Django MPTT**  pour gérer les structures arborescentes des pages FAQ et d'assistance.

Les modèles principaux sont :
- `FaqPage` : Pages FAQ avec filtrage par catégorie utilisateur
- `ContentBlock` : Blocs de contenu multimédia
- `SuggestedPage` : Relations entre pages
- `AssistancePage` : Pages d'aide avec formulaires
- `Message` : Archivage des demandes
- `Webinar` : Événements de formation

### Stockage

- **Fichiers média** : Stockage S3 privé pour les images des blocs de contenu
- **Recherche** : Extensions PostgreSQL (pg_trgm, unaccent) pour la recherche plein texte

### Contrôle d'accès

Le système respecte les catégories d'utilisateurs définies dans le module `accounts` :
- Staff Trackdéchets
- Administration centrale
- Inspecteurs ICPE
- CTT (Contrôleurs des transports)
- Inspection du travail
- Gendarmerie
- ARS
- Douane
- Observatoire

## Interface utilisateur

L'interface utilise **HTMX** pour une navigation fluide :

- Chargement dynamique des pages sans rechargement complet
- Mise à jour de l'URL lors de la navigation
- Mise en évidence automatique de la page active et dépliage éventuel du menu collapsé
- Recherche en temps réel
- Formulaires interactifs

## Administration

L'interface d'administration Django permet de :

- Réorganiser les pages par glisser-déposer
- Gérer les blocs de contenu inline
- Configurer les suggestions de pages
- Consulter les messages reçus
- Planifier et gérer les webinaires
 