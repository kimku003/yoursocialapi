from ninja import NinjaAPI, Router, Schema
from ninja.security import HttpBearer
from django.conf import settings
from django.db.models import Q, Count
from typing import List, Optional
from datetime import datetime, timedelta

from users.models import User
from social.models import Post, Story
from users.api import AuthBearer  # Import de notre classe AuthBearer personnalisée

# Création de l'instance API avec la configuration CORS
api = NinjaAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url='/docs/',
    csrf=True,
    # cors_origins=settings.CORS_ALLOWED_ORIGINS,
)

# Routeur pour les fonctionnalités globales
global_router = Router()

# Schémas pour la recherche
class SearchResultSchema(Schema):
    type: str  # 'user', 'post', 'story', 'hashtag'
    id: int
    title: str
    description: Optional[str]
    image: Optional[str]
    created_at: datetime
    relevance_score: float

class StatisticsSchema(Schema):
    total_users: int
    total_posts: int
    total_stories: int
    active_users_24h: int
    new_posts_24h: int
    new_stories_24h: int
    popular_hashtags: List[dict]

# Routes de recherche globale
@global_router.get("/search", response=List[SearchResultSchema], auth=AuthBearer())
def global_search(request, query: str, page: int = 1, limit: int = 20):
    start = (page - 1) * limit
    end = start + limit
    
    results = []
    
    # Recherche d'utilisateurs
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(bio__icontains=query)
    ).select_related('avatar')[:limit]
    
    for user in users:
        results.append({
            'type': 'user',
            'id': user.id,
            'title': user.username,
            'description': user.bio,
            'image': user.avatar.url if user.avatar else None,
            'created_at': user.date_joined,
            'relevance_score': 1.0  # À améliorer avec un système de scoring
        })
    
    # Recherche de posts
    posts = Post.objects.filter(
        Q(content__icontains=query) |
        Q(hashtags__contains=[query])
    ).select_related('author', 'media')[:limit]
    
    for post in posts:
        results.append({
            'type': 'post',
            'id': post.id,
            'title': f"Post de {post.author.username}",
            'description': post.content[:100] + '...' if len(post.content) > 100 else post.content,
            'image': post.media.url if post.media else None,
            'created_at': post.created_at,
            'relevance_score': 0.8
        })
    
    # Recherche de stories
    stories = Story.objects.filter(
        Q(caption__icontains=query) |
        Q(hashtags__contains=[query])
    ).filter(
        expires_at__gt=datetime.now()
    ).select_related('author', 'content')[:limit]
    
    for story in stories:
        results.append({
            'type': 'story',
            'id': story.id,
            'title': f"Story de {story.author.username}",
            'description': story.caption,
            'image': story.content.url if story.content else None,
            'created_at': story.created_at,
            'relevance_score': 0.7
        })
    
    # Trier par score de pertinence et date
    results.sort(key=lambda x: (-x['relevance_score'], -x['created_at'].timestamp()))
    
    return results[start:end]

# Routes pour les statistiques
@global_router.get("/statistics", response=StatisticsSchema, auth=AuthBearer())
def get_statistics(request):
    # Statistiques de base
    total_users = User.objects.count()
    total_posts = Post.objects.count()
    total_stories = Story.objects.count()
    
    # Statistiques des dernières 24h
    active_users_24h = User.objects.filter(
        last_login__gte=datetime.now() - timedelta(days=1)
    ).count()
    
    new_posts_24h = Post.objects.filter(
        created_at__gte=datetime.now() - timedelta(days=1)
    ).count()
    
    new_stories_24h = Story.objects.filter(
        created_at__gte=datetime.now() - timedelta(days=1)
    ).count()
    
    # Hashtags populaires
    hashtags = Post.objects.exclude(
        hashtags__isnull=True
    ).values_list(
        'hashtags', flat=True
    )
    
    hashtag_counts = {}
    for tags in hashtags:
        for tag in tags:
            if tag not in hashtag_counts:
                hashtag_counts[tag] = 0
            hashtag_counts[tag] += 1
    
    popular_hashtags = [
        {'tag': tag, 'count': count}
        for tag, count in sorted(
            hashtag_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
    ]
    
    return {
        'total_users': total_users,
        'total_posts': total_posts,
        'total_stories': total_stories,
        'active_users_24h': active_users_24h,
        'new_posts_24h': new_posts_24h,
        'new_stories_24h': new_stories_24h,
        'popular_hashtags': popular_hashtags
    }

# Importation et inclusion des routeurs après la création de l'API
from users.api import router as users_router
from messaging.api import router as messaging_router
from notifications.api import router as notifications_router
from social.api import router as social_router

# Ajout des routeurs à l'API
api.add_router("", users_router)
api.add_router("messaging/", messaging_router)
api.add_router("notifications/", notifications_router)
api.add_router("social/", social_router)
api.add_router("", global_router) 

