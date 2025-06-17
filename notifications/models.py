from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Notification(models.Model):
    """
    Modèle pour les notifications
    """
    NOTIFICATION_TYPES = [
        ('follow', _('Nouvel abonné')),
        ('like', _('Nouveau like')),
        ('comment', _('Nouveau commentaire')),
        ('mention', _('Mention')),
        ('message', _('Nouveau message')),
        ('story_mention', _('Mention dans une story')),
        ('story_reaction', _('Réaction à une story')),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('destinataire')
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        verbose_name=_('expéditeur'),
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        _('type de notification'),
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    content = models.TextField(_('contenu'))
    is_read = models.BooleanField(_('lu'), default=False)
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    read_at = models.DateTimeField(_('date de lecture'), null=True, blank=True)

    # Pour lier la notification à un objet spécifique (post, comment, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification pour {self.recipient.username} - {self.get_notification_type_display()}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

class NotificationPreference(models.Model):
    """
    Modèle pour les préférences de notification des utilisateurs
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('utilisateur')
    )
    email_notifications = models.BooleanField(_('notifications par email'), default=True)
    push_notifications = models.BooleanField(_('notifications push'), default=True)
    in_app_notifications = models.BooleanField(_('notifications in-app'), default=True)
    
    # Préférences par type de notification
    follow_notifications = models.BooleanField(_('notifications d\'abonnements'), default=True)
    like_notifications = models.BooleanField(_('notifications de likes'), default=True)
    comment_notifications = models.BooleanField(_('notifications de commentaires'), default=True)
    mention_notifications = models.BooleanField(_('notifications de mentions'), default=True)
    message_notifications = models.BooleanField(_('notifications de messages'), default=True)
    story_notifications = models.BooleanField(_('notifications de stories'), default=True)

    class Meta:
        verbose_name = _('préférence de notification')
        verbose_name_plural = _('préférences de notification')

    def __str__(self):
        return f"Préférences de notification de {self.user.username}"
