## Module inutilisé

L'app content dédiée au recueil de feedback utilisateur n'est plus utilisée actuellement.

## Téléchargement de fichier parquets

**Module data_exports**

Des fichiers parquet sont déposés régulièrement sur un hébergement s3 privé (les fichiers ne sont pas accessibles au
public).
La commande `manage.py retrieve_data_exports` permet de parcourir le bucket concerné et de récupérer les paths, noms,
années
et tailles des exports pour reseigner les modèles `DataExport`. Les modèles `DataExport`
permettent d'afficher la page de listing.
Au clic, une url présignée est générée et renvoyée à l'utilisateur qui télécharge ainsi le fichier recherché.

### Affichage

## Bannière configurable

Une bannière éditable visible sur toutes les pages est configurable depuis l'admin dans "Site configuration"
Le texte des pages d'accueil y est également configurable