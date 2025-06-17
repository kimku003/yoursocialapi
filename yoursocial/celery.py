import os
from celery import Celery
from django.conf import settings

# Définir le module de paramètres par défaut pour Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yoursocial.settings')

# Créer l'instance Celery
app = Celery('yoursocial')

# Charger la configuration depuis les paramètres Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches dans les applications Django
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configuration des tâches
app.conf.update(
    # Configuration du broker
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    
    # Configuration de la sérialisation
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    
    # Configuration du fuseau horaire
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    
    # Configuration des tâches périodiques
    beat_schedule=settings.CELERY_BEAT_SCHEDULE,
    
    # Configuration des workers
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Configuration des résultats
    result_expires=3600,  # 1 heure
    task_ignore_result=False,
    
    # Configuration des tâches
    task_always_eager=False,  # False en production, True en développement pour les tests
    task_eager_propagates=True,
    
    # Configuration des logs
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Tâche de test
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return 'Tâche de test exécutée avec succès'

# Tâche pour nettoyer les stories expirées
@app.task
def cleanup_expired_stories():
    """Nettoyer les stories expirées"""
    from django.utils import timezone
    from social.models import Story
    
    expired_stories = Story.objects.filter(
        expires_at__lte=timezone.now()
    )
    
    count = expired_stories.count()
    expired_stories.delete()
    
    print(f'{count} stories expirées ont été supprimées')
    return count

# Tâche pour mettre à jour les statistiques utilisateur
@app.task
def update_user_statistics():
    """Mettre à jour les statistiques de tous les utilisateurs"""
    from users.models import User
    from django.db.models import Count
    
    users = User.objects.all()
    updated_count = 0
    
    for user in users:
        # Mettre à jour le nombre de posts
        posts_count = user.posts.count()
        if user.posts_count != posts_count:
            user.posts_count = posts_count
            user.save(update_fields=['posts_count'])
            updated_count += 1
        
        # Mettre à jour le nombre de followers
        followers_count = user.followers.count()
        if user.followers_count != followers_count:
            user.followers_count = followers_count
            user.save(update_fields=['followers_count'])
            updated_count += 1
        
        # Mettre à jour le nombre de following
        following_count = user.following.count()
        if user.following_count != following_count:
            user.following_count = following_count
            user.save(update_fields=['following_count'])
            updated_count += 1
    
    print(f'Statistiques mises à jour pour {updated_count} utilisateurs')
    return updated_count

# Tâche pour envoyer un digest de notifications
@app.task
def send_notification_digest():
    """Envoyer un digest des notifications par email"""
    from django.utils import timezone
    from notifications.models import Notification
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    
    # Récupérer les notifications non lues des dernières 24h
    yesterday = timezone.now() - timezone.timedelta(days=1)
    notifications = Notification.objects.filter(
        is_read=False,
        created_at__gte=yesterday
    ).select_related('recipient', 'sender')
    
    # Grouper par utilisateur
    user_notifications = {}
    for notif in notifications:
        if notif.recipient.id not in user_notifications:
            user_notifications[notif.recipient.id] = {
                'user': notif.recipient,
                'notifications': []
            }
        user_notifications[notif.recipient.id]['notifications'].append(notif)
    
    # Envoyer un email pour chaque utilisateur
    sent_count = 0
    for user_data in user_notifications.values():
        user = user_data['user']
        user_notifs = user_data['notifications']
        
        # Vérifier si l'utilisateur a activé les notifications par email
        if hasattr(user, 'settings') and user.settings.email_notifications:
            # Préparer le contenu de l'email
            context = {
                'user': user,
                'notifications': user_notifs,
                'count': len(user_notifs)
            }
            
            # Rendu du template (vous devrez créer ces templates)
            subject = f'Vous avez {len(user_notifs)} nouvelles notifications sur YourSocial'
            html_message = render_to_string('notifications/email_digest.html', context)
            plain_message = render_to_string('notifications/email_digest.txt', context)
            
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                sent_count += 1
            except Exception as e:
                print(f'Erreur lors de l\'envoi de l\'email à {user.email}: {e}')
    
    print(f'Digest de notifications envoyé à {sent_count} utilisateurs')
    return sent_count

# Tâche pour traiter les uploads de médias
@app.task
def process_media_upload(file_path, media_type, user_id):
    """Traiter un upload de média (redimensionnement, compression, etc.)"""
    from PIL import Image
    import os
    
    try:
        if media_type == 'image':
            # Ouvrir l'image
            with Image.open(file_path) as img:
                # Convertir en RGB si nécessaire
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionner selon le type
                if 'avatar' in file_path:
                    img.thumbnail(settings.AVATAR_SIZE, Image.Resampling.LANCZOS)
                elif 'banner' in file_path:
                    img.thumbnail(settings.BANNER_SIZE, Image.Resampling.LANCZOS)
                elif 'post' in file_path:
                    img.thumbnail(settings.POST_IMAGE_SIZE, Image.Resampling.LANCZOS)
                elif 'story' in file_path:
                    img.thumbnail(settings.STORY_SIZE, Image.Resampling.LANCZOS)
                
                # Sauvegarder l'image optimisée
                img.save(file_path, 'JPEG', quality=85, optimize=True)
        
        print(f'Média traité avec succès: {file_path}')
        return True
        
    except Exception as e:
        print(f'Erreur lors du traitement du média {file_path}: {e}')
        return False

# Tâche pour générer des statistiques
@app.task
def generate_statistics():
    """Générer des statistiques globales"""
    from django.db.models import Count
    from django.utils import timezone
    from users.models import User
    from social.models import Post, Story, Like, Comment
    from messaging.models import Message, Conversation
    from notifications.models import Notification
    
    # Statistiques de base
    stats = {
        'total_users': User.objects.count(),
        'total_posts': Post.objects.count(),
        'total_stories': Story.objects.count(),
        'total_likes': Like.objects.count(),
        'total_comments': Comment.objects.count(),
        'total_messages': Message.objects.count(),
        'total_conversations': Conversation.objects.count(),
        'total_notifications': Notification.objects.count(),
    }
    
    # Statistiques des dernières 24h
    yesterday = timezone.now() - timezone.timedelta(days=1)
    stats.update({
        'new_users_24h': User.objects.filter(date_joined__gte=yesterday).count(),
        'new_posts_24h': Post.objects.filter(created_at__gte=yesterday).count(),
        'new_stories_24h': Story.objects.filter(created_at__gte=yesterday).count(),
        'new_likes_24h': Like.objects.filter(created_at__gte=yesterday).count(),
        'new_comments_24h': Comment.objects.filter(created_at__gte=yesterday).count(),
        'new_messages_24h': Message.objects.filter(created_at__gte=yesterday).count(),
    })
    
    # Utilisateurs actifs (connectés dans les dernières 24h)
    stats['active_users_24h'] = User.objects.filter(
        last_login__gte=yesterday
    ).count()
    
    # Hashtags populaires
    hashtags = Post.objects.exclude(
        hashtags__isnull=True
    ).values_list('hashtags', flat=True)
    
    hashtag_counts = {}
    for tags in hashtags:
        for tag in tags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
    
    stats['popular_hashtags'] = sorted(
        hashtag_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Sauvegarder les statistiques (vous pourriez créer un modèle pour cela)
    print('Statistiques générées:', stats)
    return stats

# Configuration des tâches avec des priorités
app.conf.task_routes = {
    'users.tasks.*': {'queue': 'users'},
    'social.tasks.*': {'queue': 'social'},
    'messaging.tasks.*': {'queue': 'messaging'},
    'notifications.tasks.*': {'queue': 'notifications'},
    '*.cleanup_expired_stories': {'queue': 'maintenance'},
    '*.update_user_statistics': {'queue': 'maintenance'},
    '*.generate_statistics': {'queue': 'maintenance'},
}

# Configuration des queues
app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_routing_key = 'default'

# Configuration des tâches avec des délais d'expiration
app.conf.task_soft_time_limit = 300  # 5 minutes
app.conf.task_time_limit = 600  # 10 minutes

# Configuration des retry
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Configuration des logs
app.conf.worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
app.conf.worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

if __name__ == '__main__':
    app.start() 