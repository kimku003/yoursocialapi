from typing import List, Optional
from ninja import Router, Schema, File
from ninja.files import UploadedFile
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from users.api import AuthBearer, PostResponseSchema
from .models import Story, StoryView, Post
from users.models import User

router = Router()

# Schémas pour les stories
class StoryCreateSchema(Schema):
    content: UploadedFile = File(...)
    content_type: str
    caption: Optional[str] = None
    mentions: Optional[List[int]] = None
    hashtags: Optional[List[str]] = None

class StoryResponseSchema(Schema):
    id: int
    author_id: int
    author_username: str
    author_avatar: Optional[str]
    content: str
    content_type: str
    caption: Optional[str]
    mentions: List[dict]
    hashtags: Optional[List[str]]
    created_at: datetime
    expires_at: datetime
    views_count: int
    has_viewed: bool

# Schémas pour les hashtags
class HashtagResponseSchema(Schema):
    tag: str
    posts_count: int
    stories_count: int
    last_used: datetime

# Routes pour les stories
@router.post("/stories", response=StoryResponseSchema, auth=AuthBearer())
def create_story(request, payload: StoryCreateSchema):
    story_data = payload.dict(exclude_unset=True)
    content = story_data.pop('content')
    mentions = story_data.pop('mentions', [])
    
    story = Story.objects.create(
        author=request.user,
        content=content,
        **story_data
    )
    
    if mentions:
        story.mentions.set(User.objects.filter(id__in=mentions))
    
    return {
        'id': story.id,
        'author_id': request.user.id,
        'author_username': request.user.username,
        'author_avatar': request.user.avatar.url if request.user.avatar else None,
        'content': story.content.url,
        'content_type': story.content_type,
        'caption': story.caption,
        'mentions': [
            {
                'id': user.id,
                'username': user.username,
                'avatar': user.avatar.url if user.avatar else None
            }
            for user in story.mentions.all()
        ],
        'hashtags': story.hashtags,
        'created_at': story.created_at,
        'expires_at': story.expires_at,
        'views_count': 0,
        'has_viewed': False
    }

@router.get("/stories", response=List[StoryResponseSchema], auth=AuthBearer())
def list_stories(request):
    # Récupérer les stories des utilisateurs suivis et de l'utilisateur courant
    # qui n'ont pas expiré
    stories = Story.objects.filter(
        Q(author=request.user) |
        Q(author__in=request.user.following.all())
    ).filter(
        expires_at__gt=timezone.now()
    ).select_related('author').prefetch_related(
        'mentions', 'views'
    ).order_by('-created_at')
    
    # Récupérer les vues de l'utilisateur courant
    user_views = {
        view.story_id: view
        for view in StoryView.objects.filter(
            story__in=stories,
            viewer=request.user
        )
    }
    
    return [
        {
            'id': story.id,
            'author_id': story.author.id,
            'author_username': story.author.username,
            'author_avatar': story.author.avatar.url if story.author.avatar else None,
            'content': story.content.url,
            'content_type': story.content_type,
            'caption': story.caption,
            'mentions': [
                {
                    'id': user.id,
                    'username': user.username,
                    'avatar': user.avatar.url if user.avatar else None
                }
                for user in story.mentions.all()
            ],
            'hashtags': story.hashtags,
            'created_at': story.created_at,
            'expires_at': story.expires_at,
            'views_count': story.views.count(),
            'has_viewed': story.id in user_views
        }
        for story in stories
    ]

@router.post("/stories/{story_id}/view", auth=AuthBearer())
def view_story(request, story_id: int):
    story = get_object_or_404(
        Story.objects.filter(
            Q(author=request.user) |
            Q(author__in=request.user.following.all())
        ).filter(
            expires_at__gt=timezone.now()
        ),
        id=story_id
    )
    
    # Créer ou récupérer la vue
    view, created = StoryView.objects.get_or_create(
        story=story,
        viewer=request.user
    )
    
    return {"status": "viewed" if created else "already viewed"}

@router.get("/stories/{story_id}/views", auth=AuthBearer())
def list_story_views(request, story_id: int):
    story = get_object_or_404(
        Story.objects.filter(author=request.user),
        id=story_id
    )
    
    views = StoryView.objects.filter(
        story=story
    ).select_related('viewer').order_by('-viewed_at')
    
    return [
        {
            'user_id': view.viewer.id,
            'username': view.viewer.username,
            'avatar': view.viewer.avatar.url if view.viewer.avatar else None,
            'viewed_at': view.viewed_at
        }
        for view in views
    ]

# Routes pour les hashtags
@router.get("/hashtags", response=List[HashtagResponseSchema], auth=AuthBearer())
def list_hashtags(request, query: Optional[str] = None, limit: int = 20):
    # Récupérer les hashtags les plus utilisés
    hashtags = Post.objects.exclude(
        hashtags__isnull=True
    ).values_list(
        'hashtags', flat=True
    )
    
    # Aplatir la liste des hashtags
    all_hashtags = []
    for tags in hashtags:
        all_hashtags.extend(tags)
    
    # Filtrer par la requête si fournie
    if query:
        all_hashtags = [tag for tag in all_hashtags if query.lower() in tag.lower()]
    
    # Compter les occurrences
    hashtag_counts = {}
    for tag in all_hashtags:
        if tag not in hashtag_counts:
            hashtag_counts[tag] = {
                'posts_count': 0,
                'stories_count': 0,
                'last_used': None
            }
        hashtag_counts[tag]['posts_count'] += 1
    
    # Ajouter les hashtags des stories
    story_hashtags = Story.objects.exclude(
        hashtags__isnull=True
    ).values_list('hashtags', flat=True)
    
    for tags in story_hashtags:
        for tag in tags:
            if tag not in hashtag_counts:
                hashtag_counts[tag] = {
                    'posts_count': 0,
                    'stories_count': 0,
                    'last_used': None
                }
            hashtag_counts[tag]['stories_count'] += 1
    
    # Trier par popularité
    sorted_hashtags = sorted(
        hashtag_counts.items(),
        key=lambda x: x[1]['posts_count'] + x[1]['stories_count'],
        reverse=True
    )[:limit]
    
    return [
        {
            'tag': tag,
            'posts_count': data['posts_count'],
            'stories_count': data['stories_count'],
            'last_used': data['last_used']
        }
        for tag, data in sorted_hashtags
    ]

@router.get("/hashtags/{tag}", response=List[PostResponseSchema], auth=AuthBearer())
def get_hashtag_posts(request, tag: str, page: int = 1, limit: int = 20):
    start = (page - 1) * limit
    end = start + limit
    
    posts = Post.objects.filter(
        hashtags__contains=[tag]
    ).select_related('author').order_by('-created_at')[start:end]
    
    return posts

@router.get("/hashtags/{tag}/stories", response=List[StoryResponseSchema], auth=AuthBearer())
def get_hashtag_stories(request, tag: str, page: int = 1, limit: int = 20):
    start = (page - 1) * limit
    end = start + limit
    
    stories = Story.objects.filter(
        hashtags__contains=[tag],
        expires_at__gt=timezone.now()
    ).select_related('author').order_by('-created_at')[start:end]
    
    return [
        {
            'id': story.id,
            'author_id': story.author.id,
            'author_username': story.author.username,
            'author_avatar': story.author.avatar.url if story.author.avatar else None,
            'content': story.content.url,
            'content_type': story.content_type,
            'caption': story.caption,
            'mentions': [
                {
                    'id': user.id,
                    'username': user.username,
                    'avatar': user.avatar.url if user.avatar else None
                }
                for user in story.mentions.all()
            ],
            'hashtags': story.hashtags,
            'created_at': story.created_at,
            'expires_at': story.expires_at,
            'views_count': story.views.count(),
            'has_viewed': False
        }
        for story in stories
    ]

# Routes pour les tendances
@router.get("/trending", auth=AuthBearer())
def get_trending_content(request, limit: int = 10):
    # Posts tendance (basé sur les likes et commentaires des dernières 24h)
    yesterday = timezone.now() - timedelta(days=1)
    
    trending_posts = Post.objects.filter(
        created_at__gte=yesterday
    ).annotate(
        engagement=Count('likes') + Count('comments')
    ).order_by('-engagement')[:limit]
    
    # Hashtags tendance
    trending_hashtags = Post.objects.filter(
        created_at__gte=yesterday
    ).exclude(
        hashtags__isnull=True
    ).values_list('hashtags', flat=True)
    
    hashtag_counts = {}
    for tags in trending_hashtags:
        for tag in tags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
    
    top_hashtags = sorted(
        hashtag_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return {
        'trending_posts': [
            {
                'id': post.id,
                'content': post.content[:100] + '...' if len(post.content) > 100 else post.content,
                'author_username': post.author.username,
                'likes_count': post.likes.count(),
                'comments_count': post.comments.count(),
                'created_at': post.created_at
            }
            for post in trending_posts
        ],
        'trending_hashtags': [
            {
                'tag': tag,
                'count': count
            }
            for tag, count in top_hashtags
        ]
    }

# Routes pour les stories expirées
@router.get("/stories/expired", auth=AuthBearer())
def get_expired_stories(request, page: int = 1, limit: int = 20):
    start = (page - 1) * limit
    end = start + limit
    
    expired_stories = Story.objects.filter(
        author=request.user,
        expires_at__lte=timezone.now()
    ).order_by('-created_at')[start:end]
    
    return [
        {
            'id': story.id,
            'content': story.content.url,
            'content_type': story.content_type,
            'caption': story.caption,
            'created_at': story.created_at,
            'expires_at': story.expires_at,
            'views_count': story.views.count()
        }
        for story in expired_stories
    ]

# Routes pour les statistiques des stories
@router.get("/stories/statistics", auth=AuthBearer())
def get_story_statistics(request):
    user = request.user
    
    # Stories actives
    active_stories = user.stories.filter(
        expires_at__gt=timezone.now()
    ).count()
    
    # Stories expirées
    expired_stories = user.stories.filter(
        expires_at__lte=timezone.now()
    ).count()
    
    # Vues totales
    total_views = StoryView.objects.filter(
        story__author=user
    ).count()
    
    # Vues des dernières 24h
    yesterday = timezone.now() - timedelta(days=1)
    views_24h = StoryView.objects.filter(
        story__author=user,
        viewed_at__gte=yesterday
    ).count()
    
    return {
        'active_stories': active_stories,
        'expired_stories': expired_stories,
        'total_views': total_views,
        'views_24h': views_24h
    } 