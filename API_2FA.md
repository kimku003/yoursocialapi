# Authentification à deux facteurs (2FA) – API YourSocial

## 1. Activer le 2FA

**POST** `/api/me/2fa/activate`

- **Headers** :
    - Authorization: Bearer <access_token>
- **Réponse** :
```json
{
  "otpauth_url": "otpauth://totp/YourSocial:test@example.com?secret=XXXX&issuer=YourSocial",
  "qr_code_base64": "iVBORw0KGgoAAAANS..."
}
```

---

## 2. Vérifier et activer le 2FA

**POST** `/api/me/2fa/verify`

- **Headers** :
    - Authorization: Bearer <access_token>
- **Body** :
```json
{
  "code": "123456"
}
```
- **Réponse** :
```json
{
  "success": true,
  "message": "2FA activé avec succès."
}
```

---

## 3. Connexion avec 2FA

**POST** `/api/login`

- **Body** :
```json
{
  "email": "test@example.com",
  "password": "testpass123",
  "code": "123456" // Optionnel, requis si 2FA activé
}
```
- **Réponse si 2FA requis mais code manquant ou invalide** :
```json
{
  "twofa_required": true,
  "message": "Code 2FA requis." // ou "Code 2FA invalide."
}
```
- **Réponse si succès** :
```json
{
  "access_token": "...",
  "refresh_token": "..."
}
```

---

## 4. Désactiver le 2FA

**POST** `/api/me/2fa/deactivate`

- **Headers** :
    - Authorization: Bearer <access_token>
- **Body** :
```json
{
  "code": "123456"
}
```
- **Réponse** :
```json
{
  "success": true,
  "message": "2FA désactivé avec succès."
}
```

---

## Limitation du nombre de tentatives de connexion (Rate Limiting)

Pour protéger l'API contre les attaques par force brute, l'endpoint de connexion est limité à 5 tentatives par 5 minutes et par adresse IP.

### Détail du fonctionnement

- **Endpoint concerné** :  
  `POST /api/login`
- **Limite** :  
  5 tentatives par 5 minutes, par IP
- **Réponse en cas de dépassement** :
```json
{
  "message": "Trop de tentatives de connexion. Veuillez réessayer plus tard."
}
```
- **Comportement** :  
  Toute nouvelle tentative depuis la même IP avant la fin du délai retournera ce message d'erreur.

### Exemple de réponse en cas de blocage

```json
{
  "message": "Trop de tentatives de connexion. Veuillez réessayer plus tard."
}
```

---

## Remarques
- Le code TOTP doit être généré par une application d'authentification (Google Authenticator, FreeOTP, etc.)
- Le QR code retourné lors de l'activation peut être scanné directement dans l'application.
- En cas de perte du code, l'utilisateur devra contacter le support pour réinitialiser le 2FA.

---

## Gestion des rôles et permissions granulaires

Pour restreindre l'accès à certaines fonctionnalités selon le rôle de l'utilisateur, utilisez le décorateur `@role_required`.

### Rôles disponibles
- ADMIN
- MODERATEUR
- UTILISATEUR
- PREMIUM

### Exemple d'utilisation dans une vue

```python
from users.permissions import role_required

@router.get("/admin/only", auth=AuthBearer())
@role_required(["ADMIN"])
def admin_only_view(request):
    return {"message": "Bienvenue, administrateur !"}
```

### Exemple pour plusieurs rôles

```python
@router.get("/moderation", auth=AuthBearer())
@role_required(["ADMIN", "MODERATEUR"])
def moderation_view(request):
    return {"message": "Bienvenue, modérateur ou admin !"}
```

### Comportement
- Si l'utilisateur n'est pas authentifié : erreur 401 (Authentification requise)
- Si l'utilisateur n'a pas le bon rôle : erreur 403 (Permission refusée)

Utilisez ce décorateur sur toutes les routes nécessitant une restriction par rôle. 