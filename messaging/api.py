from typing import List, Optional
from ninja import Router, Schema, File
from ninja.files import UploadedFile
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone

from users.api import AuthBearer
from .models import Conversation, Message, MessageReaction
from users.models import User

router = Router()

# Schémas pour la messagerie
class MessageCreateSchema(Schema):
    content: str
    media: Optional[UploadedFile] = None
    media_type: Optional[str] = None

class MessageResponseSchema(Schema):
    id: int
    conversation_id: int
    sender_id: int
    sender_username: str
    content: str
    media: Optional[str]
    media_type: Optional[str]
    is_read: bool
    created_at: datetime
    updated_at: datetime

class ConversationResponseSchema(Schema):
    id: int
    participants: List[dict]
    last_message: Optional[MessageResponseSchema]
    updated_at: datetime
    unread_count: int

class MessageReactionSchema(Schema):
    emoji: str

# Routes pour les conversations
@router.get("/conversations", response=List[ConversationResponseSchema], auth=AuthBearer())
def list_conversations(request, page: int = 1, limit: int = 20):
    start = (page - 1) * limit
    end = start + limit
    
    conversations = Conversation.objects.filter(
        participants=request.user
    ).select_related('last_message').prefetch_related('participants')[start:end]
    
    result = []
    for conv in conversations:
        unread_count = Message.objects.filter(
            conversation=conv,
            is_read=False
        ).exclude(sender=request.user).count()
        
        result.append({
            'id': conv.id,
            'participants': [
                {
                    'id': p.id,
                    'username': p.username,
                    'avatar': p.avatar.url if p.avatar else None
                }
                for p in conv.participants.all()
            ],
            'last_message': conv.last_message,
            'updated_at': conv.updated_at,
            'unread_count': unread_count
        })
    
    return result

@router.post("/conversations", response=ConversationResponseSchema, auth=AuthBearer())
def create_conversation(request, participant_id: int):
    participant = get_object_or_404(User, id=participant_id)
    
    # Vérifier si une conversation existe déjà
    existing_conv = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=participant
    ).first()
    
    if existing_conv:
        return existing_conv
    
    # Créer une nouvelle conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(request.user, participant)
    
    return {
        'id': conversation.id,
        'participants': [
            {
                'id': p.id,
                'username': p.username,
                'avatar': p.avatar.url if p.avatar else None
            }
            for p in conversation.participants.all()
        ],
        'last_message': None,
        'updated_at': conversation.updated_at,
        'unread_count': 0
    }

# Routes pour les messages
@router.post("/conversations/{conversation_id}/messages", response=MessageResponseSchema, auth=AuthBearer())
def send_message(request, conversation_id: int, payload: MessageCreateSchema):
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    message_data = payload.dict(exclude_unset=True)
    media = message_data.pop('media', None)
    
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        **message_data
    )
    
    if media:
        message.media.save(media.name, media)
    
    # Mettre à jour le dernier message de la conversation
    conversation.last_message = message
    conversation.save()
    
    return {
        'id': message.id,
        'conversation_id': conversation.id,
        'sender_id': request.user.id,
        'sender_username': request.user.username,
        'content': message.content,
        'media': message.media.url if message.media else None,
        'media_type': message.media_type,
        'is_read': message.is_read,
        'created_at': message.created_at,
        'updated_at': message.updated_at
    }

@router.get("/conversations/{conversation_id}/messages", response=List[MessageResponseSchema], auth=AuthBearer())
def list_messages(request, conversation_id: int, page: int = 1, limit: int = 50):
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    start = (page - 1) * limit
    end = start + limit
    
    messages = Message.objects.filter(
        conversation=conversation
    ).select_related('sender').order_by('-created_at')[start:end]
    
    # Marquer les messages comme lus
    unread_messages = messages.filter(is_read=False).exclude(sender=request.user)
    unread_messages.update(is_read=True, read_at=timezone.now())
    
    return [
        {
            'id': msg.id,
            'conversation_id': conversation.id,
            'sender_id': msg.sender.id,
            'sender_username': msg.sender.username,
            'content': msg.content,
            'media': msg.media.url if msg.media else None,
            'media_type': msg.media_type,
            'is_read': msg.is_read,
            'created_at': msg.created_at,
            'updated_at': msg.updated_at
        }
        for msg in messages
    ]

# Routes pour les réactions aux messages
@router.post("/messages/{message_id}/reactions", auth=AuthBearer())
def add_reaction(request, message_id: int, payload: MessageReactionSchema):
    message = get_object_or_404(
        Message.objects.filter(conversation__participants=request.user),
        id=message_id
    )
    
    reaction, created = MessageReaction.objects.get_or_create(
        message=message,
        user=request.user,
        emoji=payload.emoji
    )
    
    if not created:
        reaction.delete()
        return {"action": "removed"}
    
    return {"action": "added"}

@router.get("/messages/{message_id}/reactions", auth=AuthBearer())
def list_reactions(request, message_id: int):
    message = get_object_or_404(
        Message.objects.filter(conversation__participants=request.user),
        id=message_id
    )
    
    reactions = MessageReaction.objects.filter(
        message=message
    ).select_related('user')
    
    # Grouper par emoji
    reaction_groups = {}
    for reaction in reactions:
        if reaction.emoji not in reaction_groups:
            reaction_groups[reaction.emoji] = []
        reaction_groups[reaction.emoji].append({
            'user_id': reaction.user.id,
            'username': reaction.user.username,
            'avatar': reaction.user.avatar.url if reaction.user.avatar else None
        })
    
    return [
        {
            'emoji': emoji,
            'users': users,
            'count': len(users)
        }
        for emoji, users in reaction_groups.items()
    ]

# Routes pour la gestion des conversations
@router.delete("/conversations/{conversation_id}", auth=AuthBearer())
def delete_conversation(request, conversation_id: int):
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    # Supprimer tous les messages de la conversation
    conversation.messages.all().delete()
    conversation.delete()
    
    return {"message": "Conversation supprimée avec succès"}

@router.put("/conversations/{conversation_id}/mute", auth=AuthBearer())
def mute_conversation(request, conversation_id: int, muted: bool = True):
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    # Ici vous pourriez ajouter un champ muted au modèle Conversation
    # ou créer un modèle séparé pour les préférences de conversation
    return {"muted": muted, "message": f"Conversation {'mise en sourdine' if muted else 'réactivée'}"}

# Routes pour la gestion des messages
@router.delete("/messages/{message_id}", auth=AuthBearer())
def delete_message(request, message_id: int):
    message = get_object_or_404(
        Message.objects.filter(
            conversation__participants=request.user,
            sender=request.user
        ),
        id=message_id
    )
    
    message.delete()
    return {"message": "Message supprimé avec succès"}

@router.put("/messages/{message_id}", response=MessageResponseSchema, auth=AuthBearer())
def edit_message(request, message_id: int, content: str):
    message = get_object_or_404(
        Message.objects.filter(
            conversation__participants=request.user,
            sender=request.user
        ),
        id=message_id
    )
    
    message.content = content
    message.save()
    
    return {
        'id': message.id,
        'conversation_id': message.conversation.id,
        'sender_id': message.sender.id,
        'sender_username': message.sender.username,
        'content': message.content,
        'media': message.media.url if message.media else None,
        'media_type': message.media_type,
        'is_read': message.is_read,
        'created_at': message.created_at,
        'updated_at': message.updated_at
    }

# Routes pour les messages non lus
@router.get("/conversations/{conversation_id}/unread-count", auth=AuthBearer())
def get_unread_count(request, conversation_id: int):
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    count = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).count()
    
    return {"unread_count": count}

@router.post("/conversations/{conversation_id}/mark-read", auth=AuthBearer())
def mark_conversation_as_read(request, conversation_id: int):
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user),
        id=conversation_id
    )
    
    unread_messages = Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user)
    
    count = unread_messages.count()
    unread_messages.update(is_read=True, read_at=timezone.now())
    
    return {"marked_as_read": count}

# Routes pour les conversations récentes
@router.get("/conversations/recent", response=List[ConversationResponseSchema], auth=AuthBearer())
def get_recent_conversations(request, limit: int = 5):
    conversations = Conversation.objects.filter(
        participants=request.user
    ).select_related('last_message').prefetch_related('participants').order_by('-updated_at')[:limit]
    
    result = []
    for conv in conversations:
        unread_count = Message.objects.filter(
            conversation=conv,
            is_read=False
        ).exclude(sender=request.user).count()
        
        result.append({
            'id': conv.id,
            'participants': [
                {
                    'id': p.id,
                    'username': p.username,
                    'avatar': p.avatar.url if p.avatar else None
                }
                for p in conv.participants.all()
            ],
            'last_message': conv.last_message,
            'updated_at': conv.updated_at,
            'unread_count': unread_count
        })
    
    return result

# Routes pour les statistiques de messagerie
@router.get("/statistics", auth=AuthBearer())
def get_messaging_statistics(request):
    user = request.user
    
    # Conversations totales
    total_conversations = Conversation.objects.filter(participants=user).count()
    
    # Messages envoyés
    messages_sent = Message.objects.filter(sender=user).count()
    
    # Messages reçus
    messages_received = Message.objects.filter(
        conversation__participants=user
    ).exclude(sender=user).count()
    
    # Messages non lus
    unread_messages = Message.objects.filter(
        conversation__participants=user,
        is_read=False
    ).exclude(sender=user).count()
    
    # Messages des dernières 24h
    yesterday = timezone.now() - timedelta(days=1)
    messages_24h = Message.objects.filter(
        conversation__participants=user,
        created_at__gte=yesterday
    ).count()
    
    return {
        'total_conversations': total_conversations,
        'messages_sent': messages_sent,
        'messages_received': messages_received,
        'unread_messages': unread_messages,
        'messages_24h': messages_24h
    } 