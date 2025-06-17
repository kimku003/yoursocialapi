from typing import List, Optional
from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from users.api import AuthBearer
from .models import Notification, NotificationPreference

router = Router()

# Schémas pour les notifications
class NotificationResponseSchema(Schema):
    id: int
    notification_type: str
    content: str
    sender_id: Optional[int]
    sender_username: Optional[str]
    is_read: bool
    created_at: str
    read_at: Optional[str]
    content_object_id: Optional[int]
    content_object_type: Optional[str]

class NotificationPreferenceSchema(Schema):
    email_notifications: bool
    push_notifications: bool
    in_app_notifications: bool
    follow_notifications: bool
    like_notifications: bool
    comment_notifications: bool
    mention_notifications: bool
    message_notifications: bool
    story_notifications: bool

# Routes pour les notifications
@router.get("/notifications", response=List[NotificationResponseSchema], auth=AuthBearer())
def list_notifications(request, page: int = 1, limit: int = 20, unread_only: bool = False):
    start = (page - 1) * limit
    end = start + limit
    
    notifications = Notification.objects.filter(
        recipient=request.user
    )
    
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    notifications = notifications.select_related(
        'sender', 'content_type'
    ).order_by('-created_at')[start:end]
    
    return [
        {
            'id': notif.id,
            'notification_type': notif.notification_type,
            'content': notif.content,
            'sender_id': notif.sender.id if notif.sender else None,
            'sender_username': notif.sender.username if notif.sender else None,
            'is_read': notif.is_read,
            'created_at': notif.created_at.isoformat(),
            'read_at': notif.read_at.isoformat() if notif.read_at else None,
            'content_object_id': notif.object_id,
            'content_object_type': notif.content_type.model if notif.content_type else None
        }
        for notif in notifications
    ]

@router.post("/notifications/{notification_id}/read", auth=AuthBearer())
def mark_notification_as_read(request, notification_id: int):
    notification = get_object_or_404(
        Notification.objects.filter(recipient=request.user),
        id=notification_id
    )
    
    if not notification.is_read:
        notification.mark_as_read()
        return {"status": "marked as read"}
    
    return {"status": "already read"}

@router.post("/notifications/read-all", auth=AuthBearer())
def mark_all_notifications_as_read(request):
    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    )
    
    count = unread_notifications.count()
    unread_notifications.update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return {"marked_as_read": count}

@router.get("/notifications/unread-count", auth=AuthBearer())
def get_unread_count(request):
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    return {"unread_count": count}

# Routes pour les préférences de notification
@router.get("/notification-preferences", response=NotificationPreferenceSchema, auth=AuthBearer())
def get_notification_preferences(request):
    preferences, _ = NotificationPreference.objects.get_or_create(
        user=request.user
    )
    
    return preferences

@router.put("/notification-preferences", response=NotificationPreferenceSchema, auth=AuthBearer())
def update_notification_preferences(request, payload: NotificationPreferenceSchema):
    preferences, _ = NotificationPreference.objects.get_or_create(
        user=request.user
    )
    
    for field, value in payload.dict().items():
        setattr(preferences, field, value)
    
    preferences.save()
    return preferences 