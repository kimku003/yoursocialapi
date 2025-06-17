from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour YourSocial
    """
    email = models.EmailField(_('adresse email'), unique=True)
    bio = models.TextField(_('biographie'), max_length=500, blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', null=True, blank=True)
    banner = models.ImageField(_('bannière'), upload_to='banners/', null=True, blank=True)
    date_of_birth = models.DateField(_('date de naissance'), null=True, blank=True)
    location = models.CharField(_('localisation'), max_length=100, blank=True)
    website = models.URLField(_('site web'), max_length=200, blank=True)
    is_private = models.BooleanField(_('compte privé'), default=False)
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de modification'), auto_now=True)

    # Champs pour les statistiques
    followers_count = models.PositiveIntegerField(_('nombre d\'abonnés'), default=0)
    following_count = models.PositiveIntegerField(_('nombre d\'abonnements'), default=0)
    posts_count = models.PositiveIntegerField(_('nombre de publications'), default=0)

    # Configuration
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def follow(self, user):
        """Suivre un utilisateur"""
        if self != user:
            self.following.add(user)
            self.following_count = self.following.count()
            user.followers_count = user.followers.count()
            self.save(update_fields=['following_count'])
            user.save(update_fields=['followers_count'])

    def unfollow(self, user):
        """Ne plus suivre un utilisateur"""
        if self != user:
            self.following.remove(user)
            self.following_count = self.following.count()
            user.followers_count = user.followers.count()
            self.save(update_fields=['following_count'])
            user.save(update_fields=['followers_count'])

    def is_following(self, user):
        """Vérifier si l'utilisateur suit un autre utilisateur"""
        return self.following.filter(id=user.id).exists()

    def is_followed_by(self, user):
        """Vérifier si l'utilisateur est suivi par un autre utilisateur"""
        return self.followers.filter(id=user.id).exists()

    def get_mutual_followers(self):
        """Obtenir les utilisateurs qui suivent mutuellement"""
        return self.followers.filter(following=self)

    def update_posts_count(self):
        """Mettre à jour le nombre de posts"""
        self.posts_count = self.posts.count()
        self.save(update_fields=['posts_count'])

class UserSettings(models.Model):
    """
    Paramètres utilisateur
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    email_notifications = models.BooleanField(_('notifications par email'), default=True)
    push_notifications = models.BooleanField(_('notifications push'), default=True)
    language = models.CharField(_('langue'), max_length=10, default='fr')
    theme = models.CharField(_('thème'), max_length=20, default='light')
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de modification'), auto_now=True)

    class Meta:
        verbose_name = _('paramètre utilisateur')
        verbose_name_plural = _('paramètres utilisateur')

    def __str__(self):
        return f"Paramètres de {self.user.username}"
