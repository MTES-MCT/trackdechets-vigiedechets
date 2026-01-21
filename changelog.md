# Changelog

Les changements importants de Trackdéchets préparation inspection sont documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et le projet suit un schéma de versioning inspiré de [Calendar Versioning](https://calver.org/).

## [Date à définir]

- Ajout du tableau de bord avec intégration Metabase via tunnel SSH pour les utilisateurs STAFF_TD et ADMINISTRATION_CENTRALE
- Migration du module SSH de `sheets` vers `common` pour une meilleure réutilisabilité
- Support de plusieurs tunnels SSH (DataWarehouse et Metabase) via l'enum `SSHTarget`

## 08/01/2026

- Ajout du statut "fermé/inactif" (is_dormant) dans la vue cartographie des établissements avec affichage d'un badge dans le popup

## 15/12/2025

- Ajout nouveaux champs de profil pour les collecteurs et les processeurs de déchets à l'export de la carte des installations


## 10/12/2025

- Ajout d'un filtre par code déchet dans le tableau des flux de déchets (contexte web)

## 02/12/2025

- Suppression du module de stats de visites interne

## 30/11/2025

- Ajout des modules de faq, assistance et webinaires

## 26/11/2025

- Ajout des données de registres aux fichiers parquet des observatoires

## 11/11/2025

- Utilisation de UV comme package manager

## 03/09/2025

- Mise en place de l'onglet Sentinelle en béta

## 14/07/2025

- Migration des processors de la Fiche Etablissement de pandas vers polars.

## 04/06/2025

- Renommage en Vigidéchets

## 02/06/2025

- Ajout de la date depuis laquelle l'établissement a activé l'option d'import auto des données de traçabilité de
  déchets non dangereux vers le registre

## 29/05/2025

- Bascule vers les données registre Trackdéchets

## 07/05/2025

- Affichage de la cartographie des exutoires

## 02/05/2025

- Différentiation des établissements inscrits et non inscrits dans la cartographie

## 20/04/2025

- Téléchargement du regsitre V2 depuis l'api TD

## 22/04/2025

- Ajout de l'objectif de quantité traitée pour les installations 2760-2

## 15/04/2025

- Téléchargement des établissements sélectionnés sur la cartographie

## 08/04/2025

- Amélioration de la cartographie

## 27/03/2025

- Au premier login Proconnect, les utilisateurs sont créés (gendarmerie uniquement)

## 26/03/2025

Migration vers le nouveau DataWarehouse.

## 17/03/2025

- Correction d'un lien open ID cassé

## 05/03/2025

- Implémentation de login via Proconnect

## 25/02/2025

- Modification des permissions d'accès de l'administration centrale

## 24/02/2025

- Utilisation de mozilla-oidc pour la connexion MonAIOT

## 20/02/2025

- Suppression de la variable d'environnement permettant de sélectionner la query utilisée pour la recherche de bsds

## 11/02/2025

- Ajout d'une commande de nettoyage des fiches établissement pour gagner de l'espace db.

## 06/02/2025

- Dissociation des formulaires de création de fiche et de téléchargement de registre

## 05/02/2025

- Ajout des profils observatoires et téléchargement des fichiers parquet

## 30/01/2025

- Gestion de la quantité refusée

## 01/01/2025

- Correction de la recherche par plaque
  BSD-20250225-TEWGBTTVD
-

## 26/11/2024

- Ajout de la cartographie des établissements

## 25/11/2024

- Possibilité de télécharger un pdf d'attestation quand aucun bsd n'est trouvé lors d'un contrôle routier

## 28/10/2024

- Importation en masse d'utilisateurs depuis des fichiers xls (cf template xls)

## 21/10/2024

- utilisation de la query controlBds pour le contrôle routier

## 03/10/2024

- Recherche de BSD par identifiants

## 10/09/2024

- Flexibilisaation du contrôle routier: recherche par plaque OU par siret

## 27/08/2024

- Ajout du contrôle routier
-

## 20/08/2024

- Ajout des données RNDTS relatives aux transporteurs

## 05/08/2024

- Mise à jour de la notice

## 30/07/2024

- Ajout de composants dédiés aux Terres Excavées et Sédiments
- Ajout des sous-profils pour les installations TTR et de traitement de déchets

## 22/07/2024

- Ajout d'un composant dédié aux déchets sortants des incinérateurs

## 15/07/2024

- Ajout d'un linter de sécurité (bandit) et correction des points relevés
- Ajout de tests du workflow mon aiot

## 15/07/2024

- Ajout d'un linter de sécurité (bandit) et correction des points relevés
- Ajout de tests du workflow mon aiot

## 08/07/2024

- Ajout des alertes de traitements de déchets sans rubrique ICPE pour les déclarations aux RNDTS

## 04/07/2024

- Amélioration du dashboard

## 01/07/2024

- Ajout des requêtes de révision pour les BSDASRI

## 23/06/2024

- mise en place de l'Api

## 21/06/2024

- Ajout des données ICPExRNDTS
- Prise en charge du transport multi-modal pour le BSFF

## 27/05/2024

- Ajout des données du RNDTS

## 10/04/2024

- Téléchargement du registre Trackdéchets

## 08/04/2024

- Connexion via mon aiot

## 28/03/2024

- Ajout des révisions en cours pour chaque type de bordereau

## 20/02/2024

- Réorganisation de la mise en page ;
- Le filtre de date sur les données est maintenant plus précis ;
- La Fiche Inspection est renommée en Fiche Établissement.

## 29/01/2024

- Ajout des données sur le transport transfrontalier de déchets

## 04/01/2024

- Passage à python 3.11 et django 5, mise à jour des dépendances

## 11/12/2023

- Ajout de statistiques pour les transporteurs

## 04/12/2023

- Ajout de statistiques pour les entreprise de travaux

## 09/11/2023

- Mise à jour du mode d'emploi

## 31/10/2023

- Ajout d'un second facteur pour la connexion (code reçu par email)

## 25/09/2023

- Ajout d'un composant permettant d'avoir la liste des établissements reliés par le même SIREN.
- Ajout de la date de création de l'établissement.

## 12/09/2023

- Ajout d'un composant alertant lorsqu'un établissement traite des déchets dangereux
  sans avoir les bonnes rubriques ICPE ou en l'absence de données ICPE.

## 06/09/2023

- Ajout de nouveaux composants permettant de suivre les données ICPE de l'établissement.

## 07/08/2023

- Ajout de la possibilité de choisir l'intervalle de dates pour lequel afficher les données.

## 20/06/2023

- Ajout des composants multi-variables pour les quantités.

## 07/06/2023

- Ajout des données de contenants pour les BSFF.

## 30/05/2023

- Ajout d'une table listant les bordereaux présentant des quantités aberrantes.

## 29/05/2023

- Ajout d'une table listant les BSDA de déchets collectés chez des particuliers.

## 25/05/2023

- Corrige le problème de certains tableaux qui étaient coupés en version PDF.

## 17/05/2023

- Ajout des statistiques sur les déchets non dangereux suivis par BSDD.
- Utilise les m3 comme unité pour les DASRIs.

## 16/05/2023

- Ajout du temps de traitement moyen pour les bordereaux qui ont un traitement d'une durée supérieure à un mois.

## 11/05/2023

- Ajout d'un formulaire d'enquête.

## 04/05/2023

- Ajout d'un composant permettant de lister les bordereaux (BSDD et BSDA) pour lesquels l'établissement se positionne en
  tant qu'émetteur et destinataire et qui ont une adresse travaux renseignée.

## 03/05/2023

- Ajout de filtre de dates sur tous les data processors pour être sûr que les données soient
  comprises dans une fenêtre d'une année glissante.

## 20/04/2023

- Ajout d'un composant listant les bordereaux annulés.

## 03/04/2023

- Ajoute un composant permettant de lister les déchets indiqués comme dangereux mais qui n'ont pas de code déchets
  dangereux

## 30/03/2023

- Corrige la gestion des date manquantes sur le tableau
  icpe [#3](https://github.com/MTES-MCT/trackdechets-preparation-inspection/pull/3)
- Améliore le composant de statistiques
  déchets [#4](https://github.com/MTES-MCT/trackdechets-preparation-inspection/pull/4)
