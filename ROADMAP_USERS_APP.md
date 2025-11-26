# Feuille de Route : Amélioration de l'Application Users

Cette feuille de route décrit les améliorations et les fonctionnalités à implémenter pour l'application `users`.

## 1. Amélioration de l'Authentification

-   **Mise en place de la 2FA (authentification à deux facteurs)**:
    -   Intégration d'une solution 2FA (par exemple, TOTP via des applications comme Google Authenticator).
    -   Création des endpoints API pour l'activation, la désactivation et la vérification 2FA.
    -   Mise à jour des modèles utilisateur pour stocker les configurations 2FA.
-   **Intégration de WebAuthn pour une authentification sans mot de passe**:
    -   Ajout du support FIDO2/WebAuthn pour permettre l'authentification via des clés de sécurité ou des capteurs biométriques.
    -   Développement des endpoints API pour l'enregistrement et l'authentification WebAuthn.
-   **Gestion des sessions et des jetons JWT**:
    -   Assurer une gestion sécurisée des jetons d'accès et de rafraîchissement (Refresh Tokens).
    -   Implémenter la révocation des jetons si nécessaire.

## 2. Gestion du Profil Utilisateur

-   **Modification des informations de profil (nom, bio, photo de profil)**:
    -   Création/mise à jour des endpoints API pour permettre aux utilisateurs de modifier leurs informations de profil.
    -   Gestion des téléchargements de photos de profil (media/uploads).
-   **Gestion des paramètres de confidentialité**:
    -   Développement d'endpoints API pour gérer la visibilité du profil, les préférences de contact, etc.
-   **Option de désactivation/suppression de compte**:
    -   Création des endpoints API et de la logique métier pour permettre aux utilisateurs de désactiver temporairement ou de supprimer définitivement leur compte.

## 3. Permissions et Rôles

-   **Définition de rôles utilisateurs personnalisés (par exemple, "Modérateur", "Admin")**:
    -   Mise en place d'un système de rôles clair pour la gestion des utilisateurs.
    -   Intégration avec les permissions Django.
-   **Mise en place de permissions granulaires**:
    -   Utilisation de `django-guardian` ou d'un système similaire pour attribuer des permissions spécifiques sur des objets.

## 4. Notifications de l'Utilisateur

-   **Intégration plus poussée avec l'application notifications pour les préférences de notification spécifiques à l'utilisateur**:
    -   Extension du modèle `NotificationPreference` pour inclure plus d'options personnalisables.
    -   Endpoints API pour la gestion des préférences de notification par l'utilisateur.

## 5. Optimisation des Requêtes

-   **Revoir les requêtes de l'API `users` pour utiliser `select_related` et `prefetch_related` si nécessaire**:
    -   Analyser les endpoints existants et futurs pour identifier les requêtes N+1.
    -   Appliquer des optimisations ORM pour améliorer les performances.