from typing import List, Optional
from ninja import Router, Schema, File
from ninja.files import UploadedFile
from django.contrib.auth import get_user_model, authenticate
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ninja.security import HttpBearer
from datetime import datetime, timedelta
import jwt
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
import pyotp
import qrcode
import io
import base64
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache

from .models import User, UserSettings, User2FA
from social.models import Post, Comment, Like

# Création du routeur avec un préfixe unique
# router = Router(prefix="users")
router = Router()
User = get_user_model()

# Schémas de validation
class UserCreateSchema(Schema):
    email: str
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserUpdateSchema(Schema):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    is_private: Optional[bool] = None

class UserResponseSchema(Schema):
    id: int
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    bio: Optional[str]
    avatar: Optional[str]
    banner: Optional[str]
    location: Optional[str]
    website: Optional[str]
    is_private: bool
    followers_count: int
    following_count: int
    posts_count: int
    created_at: datetime

class TokenSchema(Schema):
    access_token: str
    refresh_token: str

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload.get('user_id')
            if not user_id:
                print(f"DEBUG: Token sans user_id: {payload}")
                return None
            
            user = User.objects.get(id=user_id)
            print(f"DEBUG: Utilisateur authentifié: {user.username} (ID: {user.id})")
            return user
        except jwt.ExpiredSignatureError:
            print("DEBUG: Token expiré")
            return None
        except jwt.InvalidTokenError as e:
            print(f"DEBUG: Token invalide: {e}")
            return None
        except User.DoesNotExist:
            print(f"DEBUG: Utilisateur avec ID {payload.get('user_id')} n'existe pas")
            return None
        except Exception as e:
            print(f"DEBUG: Erreur d'authentification: {e}")
            return None

# Schémas pour les posts et commentaires
class PostCreateSchema(Schema):
    content: str
    author_id: Optional[int] = None  # ID de l'utilisateur qui sera l'auteur du post
    media: Optional[UploadedFile] = None
    media_type: Optional[str] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[int]] = None
    location: Optional[str] = None
    is_private: Optional[bool] = False

class PostCreateForUserSchema(Schema):
    """
    Schéma simplifié pour créer un post au nom d'un utilisateur spécifique
    (sans le paramètre author_id car il est dans l'URL)
    """
    content: str
    media: Optional[UploadedFile] = None
    media_type: Optional[str] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[int]] = None
    location: Optional[str] = None
    is_private: Optional[bool] = False

class PostResponseSchema(Schema):
    id: int
    author: UserResponseSchema
    content: str
    media: Optional[str]
    media_type: Optional[str]
    hashtags: Optional[List[str]]
    location: Optional[str]
    is_private: bool
    likes_count: int
    comments_count: int
    created_at: datetime
    updated_at: datetime

class CommentCreateSchema(Schema):
    content: str
    parent_id: Optional[int] = None

class CommentResponseSchema(Schema):
    id: int
    post_id: int
    author: UserResponseSchema
    content: str
    parent_id: Optional[int]
    likes_count: int
    created_at: datetime
    updated_at: datetime

class TwoFAActivateResponseSchema(Schema):
    otpauth_url: str
    qr_code_base64: str

class TwoFAVerifySchema(Schema):
    code: str

class TwoFAVerifyResponseSchema(Schema):
    success: bool
    message: str

class LoginSchema(Schema):
    email: str
    password: str
    code: Optional[str] = None

class LoginResponseSchema(Schema):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    twofa_required: Optional[bool] = False
    message: Optional[str] = None

class TwoFADeactivateSchema(Schema):
    code: str

class TwoFADeactivateResponseSchema(Schema):
    success: bool
    message: str

# Routes d'authentification
@router.post("/register", response=TokenSchema)
def register(request, payload: UserCreateSchema):
    try:
        # Validation du mot de passe
        validate_password(payload.password)
        
        # Création de l'utilisateur
        user = User.objects.create_user(
            email=payload.email,
            username=payload.username,
            password=payload.password,
            first_name=payload.first_name or '',
            last_name=payload.last_name or ''
        )
        
        # Création des paramètres utilisateur par défaut
        UserSettings.objects.create(user=user)
        
        # Génération des tokens
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        
        return {"access_token": access_token, "refresh_token": refresh_token}
    except ValidationError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": "Erreur lors de la création du compte"}

@router.post("/login", response=LoginResponseSchema)
@ratelimit(key='ip', rate='5/5m', block=True)
def login(request, payload: LoginSchema):
    if getattr(request, 'limited', False):
        return {"message": "Trop de tentatives de connexion. Veuillez réessayer plus tard."}
    user = authenticate(email=payload.email, password=payload.password)
    if user:
        try:
            user_2fa = User2FA.objects.get(user=user)
        except User2FA.DoesNotExist:
            user_2fa = None
        if user_2fa and user_2fa.is_active:
            if not payload.code:
                return {"twofa_required": True, "message": "Code 2FA requis."}
            totp = pyotp.TOTP(user_2fa.secret)
            if not totp.verify(payload.code):
                return {"twofa_required": True, "message": "Code 2FA invalide."}
        access_token = generate_access_token(user)
        refresh_token = generate_refresh_token(user)
        return {"access_token": access_token, "refresh_token": refresh_token}
    return {"message": "Identifiants invalides."}

@router.post("/refresh", response=TokenSchema)
def refresh_token(request, refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
        user = User.objects.get(id=payload['user_id'])
        access_token = generate_access_token(user)
        new_refresh_token = generate_refresh_token(user)
        return {"access_token": access_token, "refresh_token": new_refresh_token}
    except:
        return {"error": "Token invalide"}

# Routes de gestion du profil
@router.get("/me", response=UserResponseSchema, auth=AuthBearer())
def get_me(request):
    return request.user

@router.put("/me", response=UserResponseSchema, auth=AuthBearer())
def update_me(request, payload: UserUpdateSchema):
    user = request.user
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(user, field, value)
    user.save()
    return user

@router.post("/me/avatar", response=UserResponseSchema, auth=AuthBearer())
def upload_avatar(request, file: UploadedFile = File(...)):
    user = request.user
    user.avatar.save(file.name, file)
    user.save()
    return user

@router.post("/me/banner", response=UserResponseSchema, auth=AuthBearer())
def upload_banner(request, file: UploadedFile = File(...)):
    user = request.user
    user.banner.save(file.name, file)
    user.save()
    return user

@router.get("/users/{user_id}", response=UserResponseSchema, auth=AuthBearer())
def get_user(request, user_id: int):
    return get_object_or_404(User, id=user_id)

# Routes pour les relations entre utilisateurs
@router.post("/users/{user_id}/follow", auth=AuthBearer())
def follow_user(request, user_id: int):
    if user_id == request.user.id:
        return {"error": "Vous ne pouvez pas vous suivre vous-même"}
    
    user_to_follow = get_object_or_404(User, id=user_id)
    
    if request.user in user_to_follow.followers.all():
        # Se désabonner
        request.user.following.remove(user_to_follow)
        return {"action": "unfollowed", "message": f"Vous ne suivez plus {user_to_follow.username}"}
    else:
        # S'abonner
        request.user.following.add(user_to_follow)
        return {"action": "followed", "message": f"Vous suivez maintenant {user_to_follow.username}"}

@router.get("/users/{user_id}/followers", response=List[UserResponseSchema], auth=AuthBearer())
def list_followers(request, user_id: int, page: int = 1, limit: int = 20):
    user = get_object_or_404(User, id=user_id)
    start = (page - 1) * limit
    end = start + limit
    
    followers = user.followers.all()[start:end]
    return followers

@router.get("/users/{user_id}/following", response=List[UserResponseSchema], auth=AuthBearer())
def list_following(request, user_id: int, page: int = 1, limit: int = 20):
    user = get_object_or_404(User, id=user_id)
    start = (page - 1) * limit
    end = start + limit
    
    following = user.following.all()[start:end]
    return following

# Routes pour la recherche d'utilisateurs
@router.get("/users/search", response=List[UserResponseSchema], auth=AuthBearer())
def search_users(request, query: str, page: int = 1, limit: int = 20):
    start = (page - 1) * limit
    end = start + limit
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(bio__icontains=query)
    ).exclude(id=request.user.id)[start:end]
    
    return users

# Routes pour les suggestions d'utilisateurs
@router.get("/users/suggestions", response=List[UserResponseSchema], auth=AuthBearer())
def get_user_suggestions(request, limit: int = 10):
    # Utilisateurs que l'utilisateur ne suit pas encore
    following_ids = list(request.user.following.values_list('id', flat=True))
    following_ids.append(request.user.id)
    
    suggestions = User.objects.exclude(
        id__in=following_ids
    ).order_by('-followers_count', '-date_joined')[:limit]
    
    return suggestions

# Routes pour les paramètres utilisateur
@router.get("/me/settings", auth=AuthBearer())
def get_user_settings(request):
    settings, _ = UserSettings.objects.get_or_create(user=request.user)
    return {
        'email_notifications': settings.email_notifications,
        'push_notifications': settings.push_notifications,
        'language': settings.language,
        'theme': settings.theme
    }

@router.put("/me/settings", auth=AuthBearer())
def update_user_settings(request, payload: dict):
    settings, _ = UserSettings.objects.get_or_create(user=request.user)
    
    for field, value in payload.items():
        if hasattr(settings, field):
            setattr(settings, field, value)
    
    settings.save()
    return {
        'email_notifications': settings.email_notifications,
        'push_notifications': settings.push_notifications,
        'language': settings.language,
        'theme': settings.theme
    }

# Routes pour les statistiques utilisateur
@router.get("/me/statistics", auth=AuthBearer())
def get_user_statistics(request):
    user = request.user
    
    # Statistiques de base
    stats = {
        'posts_count': user.posts.count(),
        'followers_count': user.followers.count(),
        'following_count': user.following.count(),
        'likes_received': Like.objects.filter(
            models.Q(post__author=user) | models.Q(comment__author=user)
        ).count(),
        'comments_received': Comment.objects.filter(post__author=user).count(),
        'stories_count': user.stories.count(),
        'account_age_days': (timezone.now() - user.date_joined).days
    }
    
    # Statistiques des dernières 24h
    yesterday = timezone.now() - timedelta(days=1)
    stats.update({
        'posts_24h': user.posts.filter(created_at__gte=yesterday).count(),
        'stories_24h': user.stories.filter(created_at__gte=yesterday).count(),
        'new_followers_24h': user.followers.filter(date_joined__gte=yesterday).count()
    })
    
    return stats

# Routes pour la gestion des posts
@router.post("/posts", response=PostResponseSchema, auth=AuthBearer())
def create_post(request, payload: PostCreateSchema):
    print(f"DEBUG: Création de post - Utilisateur authentifié: {request.user.username} (ID: {request.user.id})")
    print(f"DEBUG: Contenu du post: {payload.content}")
    print(f"DEBUG: Author ID demandé: {payload.author_id}")
    
    post_data = payload.dict(exclude_unset=True)
    author_id = post_data.pop('author_id', None)
    media = post_data.pop('media', None)
    mentions = post_data.pop('mentions', [])
    
    # Déterminer l'auteur du post
    if author_id:
        # Vérifier que l'utilisateur connecté a les permissions pour créer un post au nom d'un autre utilisateur
        # Seuls les superusers ou les utilisateurs avec des permissions spéciales peuvent le faire
        if not request.user.is_superuser:
            return {"error": "Vous n'avez pas les permissions pour créer un post au nom d'un autre utilisateur"}
        
        try:
            author = User.objects.get(id=author_id)
            print(f"DEBUG: Utilisation de l'auteur spécifié: {author.username} (ID: {author.id})")
        except User.DoesNotExist:
            return {"error": f"Utilisateur avec l'ID {author_id} n'existe pas"}
    else:
        # Utiliser l'utilisateur connecté comme auteur par défaut
        author = request.user
        print(f"DEBUG: Utilisation de l'utilisateur connecté comme auteur: {author.username} (ID: {author.id})")
    
    post = Post.objects.create(
        author=author,
        **post_data
    )
    
    print(f"DEBUG: Post créé avec succès - ID: {post.id}, Auteur: {post.author.username} (ID: {post.author.id})")
    
    if media:
        post.media.save(media.name, media)
    
    if mentions:
        post.mentions.set(User.objects.filter(id__in=mentions))
    
    return post

@router.post("/users/{user_id}/posts", response=PostResponseSchema, auth=AuthBearer())
def create_post_for_user(request, user_id: int, payload: PostCreateForUserSchema):
    """
    Créer un post au nom d'un utilisateur spécifique (nécessite des permissions admin)
    """
    print(f"DEBUG: Création de post pour utilisateur {user_id} - Utilisateur authentifié: {request.user.username} (ID: {request.user.id})")
    
    # Vérifier les permissions
    if not request.user.is_superuser:
        return {"error": "Vous n'avez pas les permissions pour créer un post au nom d'un autre utilisateur"}
    
    try:
        author = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": f"Utilisateur avec l'ID {user_id} n'existe pas"}
    
    post_data = payload.dict(exclude_unset=True)
    media = post_data.pop('media', None)
    mentions = post_data.pop('mentions', [])
    
    post = Post.objects.create(
        author=author,
        **post_data
    )
    
    print(f"DEBUG: Post créé avec succès pour {author.username} - ID: {post.id}")
    
    if media:
        post.media.save(media.name, media)
    
    if mentions:
        post.mentions.set(User.objects.filter(id__in=mentions))
    
    return post

@router.get("/users/{user_id}/posts", response=List[PostResponseSchema], auth=AuthBearer())
def list_user_posts(request, user_id: int, page: int = 1, limit: int = 20):
    """
    Lister les posts d'un utilisateur spécifique
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": f"Utilisateur avec l'ID {user_id} n'existe pas"}
    
    start = (page - 1) * limit
    end = start + limit
    
    # Vérifier les permissions de visibilité
    if user.is_private and request.user != user and not request.user.is_superuser:
        # Vérifier si l'utilisateur connecté suit l'utilisateur privé
        if not request.user.is_following(user):
            return {"error": "Vous n'avez pas accès aux posts de cet utilisateur privé"}
    
    posts = Post.objects.filter(author=user).select_related('author').order_by('-created_at')[start:end]
    return posts

@router.get("/posts", response=List[PostResponseSchema], auth=AuthBearer())
def list_posts(request, page: int = 1, limit: int = 20):
    start = (page - 1) * limit
    end = start + limit
    
    posts = Post.objects.filter(
        models.Q(author=request.user) |
        models.Q(author__in=request.user.following.all()) |
        models.Q(is_private=False)
    ).select_related('author').order_by('-created_at')[start:end]
    
    return posts

@router.get("/posts/{post_id}", response=PostResponseSchema, auth=AuthBearer())
def get_post(request, post_id: int):
    return get_object_or_404(Post, id=post_id)

@router.delete("/posts/{post_id}", auth=AuthBearer())
def delete_post(request, post_id: int):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    post.delete()
    return {"message": "Post supprimé avec succès"}

# Routes pour les commentaires
@router.post("/posts/{post_id}/comments", response=CommentResponseSchema, auth=AuthBearer())
def create_comment(request, post_id: int, payload: CommentCreateSchema):
    post = get_object_or_404(Post, id=post_id)
    
    comment_data = payload.dict(exclude_unset=True)
    parent_id = comment_data.pop('parent_id', None)
    
    if parent_id:
        parent = get_object_or_404(Comment, id=parent_id, post=post)
        comment_data['parent'] = parent
    
    comment = Comment.objects.create(
        post=post,
        author=request.user,
        **comment_data
    )
    
    return comment

@router.get("/posts/{post_id}/comments", response=List[CommentResponseSchema], auth=AuthBearer())
def list_comments(request, post_id: int, page: int = 1, limit: int = 20):
    post = get_object_or_404(Post, id=post_id)
    start = (page - 1) * limit
    end = start + limit
    
    comments = Comment.objects.filter(
        post=post,
        parent=None
    ).select_related('author').order_by('-created_at')[start:end]
    
    return comments

# Routes pour les likes
@router.post("/posts/{post_id}/like", auth=AuthBearer())
def like_post(request, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    
    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        like.delete()
        return {"action": "unliked", "message": "Like supprimé"}
    
    return {"action": "liked", "message": "Post liké"}

@router.post("/comments/{comment_id}/like", auth=AuthBearer())
def like_comment(request, comment_id: int):
    comment = get_object_or_404(Comment, id=comment_id)
    
    like, created = Like.objects.get_or_create(
        user=request.user,
        comment=comment
    )
    
    if not created:
        like.delete()
        return {"action": "unliked", "message": "Like supprimé"}
    
    return {"action": "liked", "message": "Commentaire liké"}

# Routes pour le 2FA
@router.post("/me/2fa/activate", response=TwoFAActivateResponseSchema, auth=AuthBearer())
def activate_2fa(request):
    user = request.user
    # Générer un secret TOTP
    secret = pyotp.random_base32()
    otpauth_url = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="YourSocial")
    # Générer le QR code
    qr = qrcode.make(otpauth_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    # Créer ou mettre à jour User2FA
    User2FA.objects.update_or_create(user=user, defaults={"secret": secret, "is_active": False})
    return {"otpauth_url": otpauth_url, "qr_code_base64": qr_code_base64}

@router.post("/me/2fa/verify", response=TwoFAVerifyResponseSchema, auth=AuthBearer())
def verify_2fa(request, payload: TwoFAVerifySchema):
    user = request.user
    try:
        user_2fa = User2FA.objects.get(user=user)
    except User2FA.DoesNotExist:
        return {"success": False, "message": "2FA non initialisé pour cet utilisateur."}
    totp = pyotp.TOTP(user_2fa.secret)
    if totp.verify(payload.code):
        user_2fa.is_active = True
        user_2fa.save()
        return {"success": True, "message": "2FA activé avec succès."}
    else:
        return {"success": False, "message": "Code TOTP invalide."}

@router.post("/me/2fa/deactivate", response=TwoFADeactivateResponseSchema, auth=AuthBearer())
def deactivate_2fa(request, payload: TwoFADeactivateSchema):
    user = request.user
    try:
        user_2fa = User2FA.objects.get(user=user)
    except User2FA.DoesNotExist:
        return {"success": False, "message": "2FA non activé pour cet utilisateur."}
    if not user_2fa.is_active:
        return {"success": False, "message": "2FA déjà désactivé."}
    totp = pyotp.TOTP(user_2fa.secret)
    if totp.verify(payload.code):
        user_2fa.is_active = False
        user_2fa.secret = ''  # Optionnel : supprimer le secret
        user_2fa.save()
        return {"success": True, "message": "2FA désactivé avec succès."}
    else:
        return {"success": False, "message": "Code TOTP invalide."}

# Fonctions utilitaires pour les tokens JWT
def generate_access_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(minutes=60),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def generate_refresh_token(user):
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256') 