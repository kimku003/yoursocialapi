from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.db.models import JSONField

class Post(models.Model):
    """
    Modèle pour les publications
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=_('auteur')
    )
    content = models.TextField(_('contenu'))
    media = models.FileField(_('média'), upload_to='posts/', null=True, blank=True)
    media_type = models.CharField(
        _('type de média'),
        max_length=10,
        choices=[
            ('image', _('Image')),
            ('video', _('Vidéo')),
            ('audio', _('Audio')),
        ],
        null=True,
        blank=True
    )
    hashtags = JSONField(
        verbose_name=_('hashtags'),
        blank=True,
        null=True,
        default=list # Default to an empty list for JSONField
    )
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='mentioned_in_posts',
        verbose_name=_('mentions'),
        blank=True
    )
    location = models.CharField(_('localisation'), max_length=100, blank=True)
    is_private = models.BooleanField(_('privé'), default=False)
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de modification'), auto_now=True)
    likes_count = models.PositiveIntegerField(_('nombre de likes'), default=0)
    comments_count = models.PositiveIntegerField(_('nombre de commentaires'), default=0)

    class Meta:
        verbose_name = _('publication')
        verbose_name_plural = _('publications')
        ordering = ['-created_at']

    def __str__(self):
        return f"Post de {self.author.username} - {self.created_at}"

class Comment(models.Model):
    """
    Modèle pour les commentaires
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('publication')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('auteur')
    )
    content = models.TextField(_('contenu'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('commentaire parent')
    )
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de modification'), auto_now=True)
    likes_count = models.PositiveIntegerField(_('nombre de likes'), default=0)

    class Meta:
        verbose_name = _('commentaire')
        verbose_name_plural = _('commentaires')
        ordering = ['created_at']

    def __str__(self):
        return f"Commentaire de {self.author.username} sur {self.post}"

class Like(models.Model):
    """
    Modèle pour les likes (posts et commentaires)
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_('utilisateur')
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
        null=True,
        blank=True,
        verbose_name=_('publication')
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes',
        null=True,
        blank=True,
        verbose_name=_('commentaire')
    )
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)

    class Meta:
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        unique_together = [
            ('user', 'post'),
            ('user', 'comment')
        ]

    def __str__(self):
        if self.post:
            return f"Like de {self.user.username} sur {self.post}"
        return f"Like de {self.user.username} sur {self.comment}"

class Story(models.Model):
    """
    Modèle pour les stories (disparaissent après 24h)
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stories',
        verbose_name=_('auteur')
    )
    content = models.FileField(_('contenu'), upload_to='stories/')
    content_type = models.CharField(
        _('type de contenu'),
        max_length=10,
        choices=[
            ('image', _('Image')),
            ('video', _('Vidéo')),
        ]
    )
    caption = models.CharField(_('légende'), max_length=200, blank=True)
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='mentioned_in_stories',
        verbose_name=_('mentions'),
        blank=True
    )
    hashtags = JSONField(
        verbose_name=_('hashtags'),
        blank=True,
        null=True,
        default=list # Default to an empty list for JSONField
    )
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    expires_at = models.DateTimeField(_('date d\'expiration'))

    class Meta:
        verbose_name = _('story')
        verbose_name_plural = _('stories')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Story de {self.author.username} - {self.created_at}"

class StoryView(models.Model):
    """
    Modèle pour suivre qui a vu une story
    """
    story = models.ForeignKey(
        Story,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name=_('story')
    )
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='story_views',
        verbose_name=_('spectateur')
    )
    viewed_at = models.DateTimeField(_('date de visualisation'), auto_now_add=True)

    class Meta:
        verbose_name = _('visualisation de story')
        verbose_name_plural = _('visualisations de stories')
        unique_together = ['story', 'viewer']

    def __str__(self):
        return f"{self.viewer.username} a vu la story de {self.story.author.username}"