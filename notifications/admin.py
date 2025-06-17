from django.contrib import admin
from .models import Notification, NotificationPreference

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'notification_type', 'is_read', 'created_at', 'read_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'sender__username', 'content')
    date_hierarchy = 'created_at'

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'push_notifications', 'in_app_notifications')
    list_filter = ('email_notifications', 'push_notifications', 'in_app_notifications')
    search_fields = ('user__username',)
    fieldsets = (
        ('Notifications générales', {
            'fields': ('email_notifications', 'push_notifications', 'in_app_notifications')
        }),
        ('Préférences par type', {
            'fields': (
                'follow_notifications',
                'like_notifications',
                'comment_notifications',
                'mention_notifications',
                'message_notifications',
                'story_notifications'
            )
        }),
    )
