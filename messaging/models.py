from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone

class Conversation(models.Model):
    """
    Modèle pour les conversations privées
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        verbose_name=_('participants')
    )
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de modification'), auto_now=True)
    last_message = models.ForeignKey(
        'Message',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_message_in_conversation',
        verbose_name=_('dernier message')
    )

    class Meta:
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation entre {', '.join(p.username for p in self.participants.all())}"

class Message(models.Model):
    """
    Modèle pour les messages privés
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('conversation')
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('expéditeur')
    )
    content = models.TextField(_('contenu'))
    media = models.FileField(_('média'), upload_to='messages/', null=True, blank=True)
    media_type = models.CharField(
        _('type de média'),
        max_length=10,
        choices=[
            ('image', _('Image')),
            ('video', _('Vidéo')),
            ('audio', _('Audio')),
            ('file', _('Fichier')),
        ],
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('date de modification'), auto_now=True)
    is_read = models.BooleanField(_('lu'), default=False)
    read_at = models.DateTimeField(_('date de lecture'), null=True, blank=True)

    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['created_at']

    def __str__(self):
        return f"Message de {self.sender.username} dans {self.conversation}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

class MessageReaction(models.Model):
    """
    Modèle pour les réactions aux messages
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name=_('message')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_reactions',
        verbose_name=_('utilisateur')
    )
    emoji = models.CharField(_('emoji'), max_length=10)
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)

    class Meta:
        verbose_name = _('réaction')
        verbose_name_plural = _('réactions')
        unique_together = ['message', 'user', 'emoji']

    def __str__(self):
        return f"{self.user.username} a réagi avec {self.emoji} à {self.message}"
