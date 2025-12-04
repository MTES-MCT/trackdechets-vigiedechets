# Documentation - Gestion des Utilisateurs

## Vue d'ensemble

L'application utilise un système de gestion des utilisateurs avec authentification multi-facteurs et support OIDC (
OpenID Connect) pour MonAIOT et Proconnect.

## Modèle Utilisateur

### Modèle `User`

#### Champs spécifiques

- **user_type** : Type d'utilisateur (`HUMAN` ou `API`)
- **user_category** : Catégorie professionnelle de l'utilisateur
- **oidc_connexion** : Type de connexion OIDC utilisée (`MONAIOT` ou `PROCONNECT`)
- **oidc_signup** : Type d'inscription OIDC utilisée

### Catégories d'utilisateurs

Les catégories déterminent les permissions d'accès aux différentes fonctionnalités :

- **STAFF_TD** : Staff Trackdéchets (accès complet)
- **ADMINISTRATION_CENTRALE** : Administration centrale
- **INSPECTEUR_ICPE** : Inspecteur ICPE
- **CTT** : Contrôleur des transports routiers
- **INSPECTION_TRAVAIL** : Inspection du travail
- **GENDARMERIE** : Gendarmerie
- **ARS** : Agence Régionale de Santé
- **DOUANE** : Douane
- **OBSERVATOIRE** : Observatoire

| Profil                      | Fiche + registre | Contrôle routier | Bordereau | Cartographie | Situation anormale | Observatoires | Cartographie des exutoires | Vigiedéchets* | Accès admin |
|-----------------------------|------------------|------------------|-----------|--------------|--------------------|---------------|----------------------------|---------------|-------------|
| **Staff Track déchets**     | ✅                | ✅                | ✅         | ✅            | ✅                  | ✅             | ✅                          | ❌             | ✅           |
| **Administration centrale** | ✅                | ✅                | ✅         | ✅            | ✅                  | ✅             | ✅                          | ❌             | ❌           |
| **Inspecteur ICPE**         | ✅                | ✅                | ✅         | ✅            | ✅                  | ❌             | ✅                          | ❌             | ❌           |
| **CTT**                     | ✅                | ✅                | ✅         | ✅            | ❌                  | ❌             | ❌                          | ❌             | ❌           |
| **Inspection du travail**   | ✅                | ❌                | ✅         | ✅            | ❌                  | ❌             | ❌                          | ❌             | ❌           |
| **Gendarmerie**             | ✅                | ✅                | ✅         | ✅            | ✅                  | ✅             | ✅                          | ❌             | ❌           |
| **ARS**                     | ✅                | ❌                | ✅         | ✅            | ❌                  | ❌             | ❌                          | ❌             | ❌           |
| **Douanes**                 | ✅                | ✅                | ✅         | ✅            | ✅                  | ❌             | ✅                          | ❌             | ❌           |
| **Observatoires**           | ❌                | ❌                | ❌         | ✅            | ❌                  | ✅             | ❌                          | ❌             | ❌           |

* En beta, accès par ajout des comptes dans `ALLOWED_USER_FOR_SENTINEL`

## Méthodes d'authentification

### 1. Authentification par email/mot de passe + 2FA

**Processus** :

1. L'utilisateur saisit son email et mot de passe
2. Si valide, un code OTP à 6 chiffres est envoyé par email
3. L'utilisateur saisit le code pour finaliser la connexion
4. Le code est valide pendant 10 minutes (configurable via `OTP_EMAIL_TOKEN_VALIDITY`)

**Restrictions** :

- Les utilisateurs ayant utilisé OIDC pour s'inscrire ou se connecter **ne peuvent pas** utiliser cette méthode
- Backend : `accounts.backends.RestrictedLoginBackend`

### 2. Authentification OIDC

Deux fournisseurs OIDC sont supportés :

#### MonAIOT

- Backend : `oidc.backends.MonAiotOidcBackend`
- URL de callback : `/oidc/monaiot/callback/`

#### ProConnect

- Backend : `oidc.backends.ProconnectOidcBackend`
- URL de callback : `/oidc/proconnect/callback/`
- Restreint aux utilisateurs de la catégorie `GENDARMERIE`
- Vérifie l'IDP ID contre une liste autorisée

## Système de permissions

### Mixin `FullyLoggedMixin`

Ce mixin personnalisé (`common.mixins.FullyLoggedMixin`) contrôle l'accès aux vues selon :

1. **Authentification complète** : vérifie que l'utilisateur a terminé le 2FA OU vient d'OIDC
2. **Catégorie d'utilisateur** : vérifie que l'utilisateur appartient aux catégories autorisées
3. **Email spécifique** : alternative aux catégories, liste d'emails autorisés

**Utilisation** :

```python
class MyView(FullyLoggedMixin, View):
    allowed_user_categories = [
        UserCategoryChoice.STAFF_TD,
        UserCategoryChoice.INSPECTEUR_ICPE,
    ]
    # OU
    allowed_user_emails = ["user1@example.fr", "user2@example.fr"]
```

**Comportement** :

- Utilisateurs non connectés → redirection vers login
- Utilisateurs connectés sans 2FA → redirection vers page 2FA
- Utilisateurs sans permission → erreur 403

**Bypass** : Les utilisateurs avec `is_staff=True` contournent automatiquement les restrictions de catégorie/email.

### Matrices de permissions

Les permissions pour chaque fonctionnalité sont définies dans `accounts.constants` :

### Génération du menu

Le menu de navigation (`accounts.menus`) utilise des classes personnalisées :

- **`PermsItem`** : affiche l'élément si l'utilisateur est staff OU dans les catégories autorisées
- **`UserEmailItem`** : affiche l'élément si l'utilisateur est staff OU son email est dans la liste
- **`StaffMenuItem`** : affiche l'élément uniquement pour le staff

## Administration des utilisateurs

### Interface d'administration

L'interface d'admin est enrichie avec django-grappelli.

**Fonctionnalités** :

1. **Import/Export** : support d'import en masse via CSV/Excel (cf. template à la base du dépôt)
2. **Recherche** : par username et email
3. **Filtres** : staff, superuser, actif, type, catégorie, date d'inscription
4. **Action personnalisée** : envoi d'emails d'invitation

### Import d'utilisateurs

**Classe** : `accounts.admin.UserResource`

**Processus** :

1. Vérifie la présence de `user_category` (obligatoire)
2. Génère le `username` à partir de prénom + nom
3. Ignore les utilisateurs déjà existants (vérification par email)
4. Crée un UUID pour l'ID
5. Génère un mot de passe temporaire (UUID)
6. Met l'email en minuscules
7. Configure le type utilisateur sur `HUMAN`

**Champs requis pour l'import** :

- `email`
- `first_name`
- `last_name`
- `user_category`

### Envoi d'invitations

**Action** : `send_invitation_email`

**Fonctionnement** :

1. Sélectionner les utilisateurs dans l'admin
2. Lancer l'action "Send invitation email"
3. Les utilisateurs n'ayant jamais eu de `last_login` et n'étant pas OIDC reçoivent un email
4. L'email contient un lien vers la réinitialisation de mot de passe

**Exclusions** :

- Utilisateurs ayant déjà un `last_login`
- Utilisateurs OIDC (`oidc_signup` ou `oidc_connexion` défini)

## Réinitialisation de mot de passe

**Formulaire** : `accounts.forms.RestrictedPasswordResetForm`

**Restrictions** :

- Seuls les utilisateurs **non-OIDC** peuvent réinitialiser leur mot de passe
- Les utilisateurs OIDC reçoivent un message d'erreur

**Processus** :

1. Saisie de l'email
2. Vérification que l'utilisateur peut utiliser le mot de passe
3. Envoi d'un email avec lien temporaire (validité : 12 heures)
4. Définition du nouveau mot de passe

## Sécurité

### Protection contre les attaques

**Django Defender** :

- Limite les tentatives de connexion : 3 essais par IP et par username
- Verrouillage temporaire : 5 minutes
- Template personnalisé : `accounts/lockout.html`

**Throttling OTP** :

- Délai entre deux demandes d'OTP : 5 minutes (300 secondes)
- Stocké dans Redis avec clé : `otp_email_sent_{user.id}`
- Empêche le spam d'emails

### Sessions

**Configuration production** :

- Durée de session : 4 heures
- Cookie sécurisé (HTTPS uniquement)
- Protection CSRF

## Middleware OIDC

**Classe** : `oidc.middleware.OidcMiddleware`

**Rôle** : Ajoute des méthodes helper à l'objet `request.user` :

## Bonnes pratiques

1. **Toujours utiliser `FullyLoggedMixin`** pour protéger les vues
2. **Définir `allowed_user_categories`** explicitement pour chaque vue
3. **Tester les permissions** pour chaque catégorie d'utilisateur
4. **Ne pas modifier `is_staff`** pour des utilisateurs normaux (réservé aux super-admins)
   ent rédigé pour Vigiedéchets - Trackdéchets*