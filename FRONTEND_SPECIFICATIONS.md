# Spécifications Frontend - YourSocial API

## Vue d'ensemble

Ce document détaille l'API YourSocial pour le développement frontend. En attendant l'API réelle, utilisez des fichiers JSON pour simuler les réponses.

## Base URL
```
http://localhost:8000/api/
```

## Authentification

### Format des tokens
```javascript
// Stocker dans localStorage ou sessionStorage
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Headers requis
```javascript
headers: {
  'Authorization': 'Bearer ' + accessToken,
  'Content-Type': 'application/json'
}
```

## Endpoints et Schémas de données

### 1. Authentification

#### POST /register
**Corps de la requête :**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "first_name": "Prénom",
  "last_name": "Nom"
}
```

**Réponse :**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST /login
**Paramètres :**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Réponse :**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST /refresh
**Paramètres :**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2. Gestion des utilisateurs

#### GET /me
**Réponse :**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "first_name": "Prénom",
  "last_name": "Nom",
  "bio": "Ma bio",
  "avatar": "/media/avatars/avatar.jpg",
  "banner": "/media/banners/banner.jpg",
  "location": "Paris, France",
  "website": "https://monsite.com",
  "is_private": false,
  "followers_count": 150,
  "following_count": 89,
  "posts_count": 42,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### PUT /me
**Corps de la requête :**
```json
{
  "first_name": "Nouveau prénom",
  "last_name": "Nouveau nom",
  "bio": "Ma nouvelle bio",
  "location": "Lyon, France",
  "website": "https://nouveausite.com",
  "is_private": false
}
```

#### POST /me/avatar
**Corps de la requête :**
```javascript
// FormData avec fichier
const formData = new FormData();
formData.append('file', fileInput.files[0]);
```

#### GET /users/{user_id}
**Réponse :**
```json
{
  "id": 2,
  "email": "other@example.com",
  "username": "otheruser",
  "first_name": "Autre",
  "last_name": "Utilisateur",
  "bio": "Bio de l'autre utilisateur",
  "avatar": "/media/avatars/other_avatar.jpg",
  "banner": "/media/banners/other_banner.jpg",
  "location": "Marseille, France",
  "website": "https://autresite.com",
  "is_private": false,
  "followers_count": 75,
  "following_count": 120,
  "posts_count": 28,
  "created_at": "2024-01-10T14:20:00Z"
}
```

#### POST /users/{user_id}/follow
**Réponse :**
```json
{
  "action": "followed",
  "message": "Vous suivez maintenant otheruser"
}
```

#### GET /users/{user_id}/followers
**Réponse :**
```json
[
  {
    "id": 3,
    "email": "follower@example.com",
    "username": "follower",
    "first_name": "Follower",
    "last_name": "User",
    "bio": "Je suis un follower",
    "avatar": "/media/avatars/follower.jpg",
    "banner": null,
    "location": "Nice, France",
    "website": "",
    "is_private": false,
    "followers_count": 25,
    "following_count": 45,
    "posts_count": 12,
    "created_at": "2024-01-05T09:15:00Z"
  }
]
```

#### GET /users/search?query=john
**Réponse :**
```json
[
  {
    "id": 4,
    "email": "john@example.com",
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "bio": "Hello, I'm John!",
    "avatar": "/media/avatars/john.jpg",
    "banner": null,
    "location": "London, UK",
    "website": "",
    "is_private": false,
    "followers_count": 89,
    "following_count": 67,
    "posts_count": 34,
    "created_at": "2024-01-12T16:45:00Z"
  }
]
```

#### GET /users/suggestions
**Réponse :**
```json
[
  {
    "id": 5,
    "email": "suggested@example.com",
    "username": "suggested_user",
    "first_name": "Suggested",
    "last_name": "User",
    "bio": "You might know me",
    "avatar": "/media/avatars/suggested.jpg",
    "banner": null,
    "location": "Berlin, Germany",
    "website": "",
    "is_private": false,
    "followers_count": 234,
    "following_count": 156,
    "posts_count": 67,
    "created_at": "2024-01-08T11:30:00Z"
  }
]
```

### 3. Publications (Posts)

#### POST /posts
**Corps de la requête :**
```json
{
  "content": "Contenu de ma publication",
  "media": null,
  "media_type": "image",
  "hashtags": ["hashtag1", "hashtag2"],
  "mentions": [1, 2, 3],
  "location": "Paris, France",
  "is_private": false
}
```

**Réponse :**
```json
{
  "id": 1,
  "author": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "first_name": "Prénom",
    "last_name": "Nom",
    "bio": "Ma bio",
    "avatar": "/media/avatars/avatar.jpg",
    "banner": "/media/banners/banner.jpg",
    "location": "Paris, France",
    "website": "https://monsite.com",
    "is_private": false,
    "followers_count": 150,
    "following_count": 89,
    "posts_count": 42,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "content": "Contenu de ma publication",
  "media": "/media/posts/post_image.jpg",
  "media_type": "image",
  "hashtags": ["hashtag1", "hashtag2"],
  "location": "Paris, France",
  "is_private": false,
  "likes_count": 0,
  "comments_count": 0,
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

#### GET /posts
**Réponse :**
```json
[
  {
    "id": 1,
    "author": {
      "id": 1,
      "username": "username",
      "first_name": "Prénom",
      "last_name": "Nom",
      "avatar": "/media/avatars/avatar.jpg"
    },
    "content": "Contenu de ma publication",
    "media": "/media/posts/post_image.jpg",
    "media_type": "image",
    "hashtags": ["hashtag1", "hashtag2"],
    "location": "Paris, France",
    "is_private": false,
    "likes_count": 15,
    "comments_count": 3,
    "created_at": "2024-01-15T12:00:00Z",
    "updated_at": "2024-01-15T12:00:00Z"
  }
]
```

#### POST /posts/{post_id}/comments
**Corps de la requête :**
```json
{
  "content": "Mon commentaire",
  "parent_id": null
}
```

**Réponse :**
```json
{
  "id": 1,
  "post_id": 1,
  "author": {
    "id": 2,
    "username": "otheruser",
    "first_name": "Autre",
    "last_name": "Utilisateur",
    "avatar": "/media/avatars/other_avatar.jpg"
  },
  "content": "Mon commentaire",
  "parent_id": null,
  "likes_count": 0,
  "created_at": "2024-01-15T12:30:00Z",
  "updated_at": "2024-01-15T12:30:00Z"
}
```

#### GET /posts/{post_id}/comments
**Réponse :**
```json
[
  {
    "id": 1,
    "post_id": 1,
    "author": {
      "id": 2,
      "username": "otheruser",
      "first_name": "Autre",
      "last_name": "Utilisateur",
      "avatar": "/media/avatars/other_avatar.jpg"
    },
    "content": "Mon commentaire",
    "parent_id": null,
    "likes_count": 2,
    "created_at": "2024-01-15T12:30:00Z",
    "updated_at": "2024-01-15T12:30:00Z"
  }
]
```

#### POST /posts/{post_id}/like
**Réponse :**
```json
{
  "action": "liked",
  "message": "Post liké"
}
```

### 4. Stories

#### POST /social/stories
**Corps de la requête :**
```javascript
// FormData avec fichier
const formData = new FormData();
formData.append('content', fileInput.files[0]);
formData.append('content_type', 'image');
formData.append('caption', 'Légende de ma story');
formData.append('mentions', JSON.stringify([1, 2]));
formData.append('hashtags', JSON.stringify(['story', 'fun']));
```

**Réponse :**
```json
{
  "id": 1,
  "author_id": 1,
  "author_username": "username",
  "author_avatar": "/media/avatars/avatar.jpg",
  "content": "/media/stories/story_image.jpg",
  "content_type": "image",
  "caption": "Légende de ma story",
  "mentions": [
    {
      "id": 1,
      "username": "username",
      "avatar": "/media/avatars/avatar.jpg"
    },
    {
      "id": 2,
      "username": "otheruser",
      "avatar": "/media/avatars/other_avatar.jpg"
    }
  ],
  "hashtags": ["story", "fun"],
  "created_at": "2024-01-15T12:00:00Z",
  "expires_at": "2024-01-16T12:00:00Z",
  "views_count": 0,
  "has_viewed": false
}
```

#### GET /social/stories
**Réponse :**
```json
[
  {
    "id": 1,
    "author_id": 1,
    "author_username": "username",
    "author_avatar": "/media/avatars/avatar.jpg",
    "content": "/media/stories/story_image.jpg",
    "content_type": "image",
    "caption": "Légende de ma story",
    "mentions": [],
    "hashtags": ["story", "fun"],
    "created_at": "2024-01-15T12:00:00Z",
    "expires_at": "2024-01-16T12:00:00Z",
    "views_count": 5,
    "has_viewed": true
  }
]
```

#### POST /social/stories/{story_id}/view
**Réponse :**
```json
{
  "status": "viewed"
}
```

### 5. Hashtags

#### GET /social/hashtags
**Réponse :**
```json
[
  {
    "tag": "hashtag1",
    "posts_count": 15,
    "stories_count": 3,
    "last_used": "2024-01-15T12:00:00Z"
  },
  {
    "tag": "hashtag2",
    "posts_count": 8,
    "stories_count": 1,
    "last_used": "2024-01-14T18:30:00Z"
  }
]
```

#### GET /social/hashtags/{tag}
**Réponse :**
```json
[
  {
    "id": 1,
    "author": {
      "id": 1,
      "username": "username",
      "first_name": "Prénom",
      "last_name": "Nom",
      "avatar": "/media/avatars/avatar.jpg"
    },
    "content": "Contenu avec #hashtag1",
    "media": "/media/posts/post_image.jpg",
    "media_type": "image",
    "hashtags": ["hashtag1"],
    "location": "Paris, France",
    "is_private": false,
    "likes_count": 15,
    "comments_count": 3,
    "created_at": "2024-01-15T12:00:00Z",
    "updated_at": "2024-01-15T12:00:00Z"
  }
]
```

### 6. Tendances

#### GET /social/trending
**Réponse :**
```json
{
  "trending_posts": [
    {
      "id": 1,
      "content": "Contenu populaire...",
      "author_username": "username",
      "likes_count": 150,
      "comments_count": 25,
      "created_at": "2024-01-15T12:00:00Z"
    }
  ],
  "trending_hashtags": [
    {
      "tag": "trending",
      "count": 45
    }
  ]
}
```

### 7. Messagerie

#### GET /messaging/conversations
**Réponse :**
```json
[
  {
    "id": 1,
    "participants": [
      {
        "id": 1,
        "username": "username",
        "avatar": "/media/avatars/avatar.jpg"
      },
      {
        "id": 2,
        "username": "otheruser",
        "avatar": "/media/avatars/other_avatar.jpg"
      }
    ],
    "last_message": {
      "id": 5,
      "conversation_id": 1,
      "sender_id": 2,
      "sender_username": "otheruser",
      "content": "Salut !",
      "media": null,
      "media_type": null,
      "is_read": false,
      "created_at": "2024-01-15T12:00:00Z",
      "updated_at": "2024-01-15T12:00:00Z"
    },
    "updated_at": "2024-01-15T12:00:00Z",
    "unread_count": 1
  }
]
```

#### POST /messaging/conversations
**Corps de la requête :**
```json
{
  "participant_id": 2
}
```

#### GET /messaging/conversations/{conversation_id}/messages
**Réponse :**
```json
[
  {
    "id": 1,
    "conversation_id": 1,
    "sender_id": 1,
    "sender_username": "username",
    "content": "Bonjour !",
    "media": null,
    "media_type": null,
    "is_read": true,
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  },
  {
    "id": 2,
    "conversation_id": 1,
    "sender_id": 2,
    "sender_username": "otheruser",
    "content": "Salut !",
    "media": null,
    "media_type": null,
    "is_read": false,
    "created_at": "2024-01-15T12:00:00Z",
    "updated_at": "2024-01-15T12:00:00Z"
  }
]
```

#### POST /messaging/conversations/{conversation_id}/messages
**Corps de la requête :**
```json
{
  "content": "Mon message",
  "media": null,
  "media_type": "image"
}
```

### 8. Notifications

#### GET /notifications/notifications
**Réponse :**
```json
[
  {
    "id": 1,
    "notification_type": "like",
    "content": "otheruser a aimé votre publication",
    "sender_id": 2,
    "sender_username": "otheruser",
    "is_read": false,
    "created_at": "2024-01-15T12:00:00Z",
    "read_at": null,
    "content_object_id": 1,
    "content_object_type": "post"
  }
]
```

#### GET /notifications/notifications/unread-count
**Réponse :**
```json
{
  "unread_count": 5
}
```

#### GET /notifications/notification-preferences
**Réponse :**
```json
{
  "email_notifications": true,
  "push_notifications": true,
  "in_app_notifications": true,
  "follow_notifications": true,
  "like_notifications": true,
  "comment_notifications": true,
  "mention_notifications": true,
  "message_notifications": true,
  "story_notifications": true
}
```

### 9. Fonctionnalités globales

#### GET /search?query=terme
**Réponse :**
```json
[
  {
    "type": "user",
    "id": 1,
    "title": "username",
    "description": "Ma bio",
    "image": "/media/avatars/avatar.jpg",
    "created_at": "2024-01-15T10:30:00Z",
    "relevance_score": 1.0
  },
  {
    "type": "post",
    "id": 1,
    "title": "Post de username",
    "description": "Contenu de ma publication...",
    "image": "/media/posts/post_image.jpg",
    "created_at": "2024-01-15T12:00:00Z",
    "relevance_score": 0.8
  }
]
```

#### GET /statistics
**Réponse :**
```json
{
  "total_users": 1250,
  "total_posts": 5670,
  "total_stories": 890,
  "active_users_24h": 450,
  "new_posts_24h": 120,
  "new_stories_24h": 45,
  "popular_hashtags": [
    {
      "tag": "trending",
      "count": 234
    },
    {
      "tag": "fun",
      "count": 156
    }
  ]
}
```

## Codes de statut HTTP

- `200` : Succès
- `201` : Créé avec succès
- `400` : Requête invalide
- `401` : Non authentifié
- `403` : Accès interdit
- `404` : Ressource non trouvée
- `500` : Erreur serveur interne

## Pagination

La plupart des endpoints de liste supportent la pagination :
```
GET /posts?page=1&limit=20
```

## Gestion des erreurs

**Format d'erreur :**
```json
{
  "error": "Message d'erreur",
  "details": "Détails supplémentaires (optionnel)"
}
```

## Exemples d'utilisation

### Authentification
```javascript
// Login
const response = await fetch('/api/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const data = await response.json();
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
```

### Requête authentifiée
```javascript
const token = localStorage.getItem('access_token');
const response = await fetch('/api/me', {
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  }
});
```

### Upload de fichier
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/me/avatar', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token
  },
  body: formData
});
```

## Fichiers JSON de simulation

Créez des fichiers JSON dans votre projet frontend pour simuler les réponses de l'API :

```
frontend/
├── mock/
│   ├── auth.json
│   ├── users.json
│   ├── posts.json
│   ├── stories.json
│   ├── messages.json
│   ├── notifications.json
│   └── search.json
```

Exemple de structure pour `mock/users.json` :
```json
{
  "current_user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "first_name": "Prénom",
    "last_name": "Nom",
    "bio": "Ma bio",
    "avatar": "/media/avatars/avatar.jpg",
    "banner": "/media/banners/banner.jpg",
    "location": "Paris, France",
    "website": "https://monsite.com",
    "is_private": false,
    "followers_count": 150,
    "following_count": 89,
    "posts_count": 42,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "users": [
    {
      "id": 2,
      "username": "otheruser",
      "first_name": "Autre",
      "last_name": "Utilisateur",
      "avatar": "/media/avatars/other_avatar.jpg"
    }
  ]
}
```

## Notes importantes

1. **Authentification** : Tous les endpoints protégés nécessitent le header `Authorization: Bearer <token>`
2. **Pagination** : Utilisez `page` et `limit` pour la pagination
3. **Uploads** : Utilisez `FormData` pour les uploads de fichiers
4. **Gestion des erreurs** : Gérez toujours les codes de statut HTTP
5. **Refresh token** : Implémentez la logique de rafraîchissement automatique des tokens
6. **Cache** : Mettez en cache les données utilisateur et les posts pour de meilleures performances

## Prochaines étapes

1. Créez les fichiers JSON de simulation
2. Implémentez un service API pour gérer les requêtes
3. Créez les composants UI pour chaque fonctionnalité
4. Ajoutez la gestion d'état (Redux, Zustand, etc.)
5. Implémentez la gestion des erreurs et le loading
6. Ajoutez les tests unitaires pour les composants 