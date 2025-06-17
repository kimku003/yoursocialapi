from django.contrib import admin
from .models import Conversation, Message, MessageReaction

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at', 'get_participants')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('participants__username',)
    date_hierarchy = 'created_at'

    def get_participants(self, obj):
        return ", ".join([p.username for p in obj.participants.all()])
    get_participants.short_description = 'Participants'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'conversation', 'content', 'created_at', 'is_read', 'read_at')
    list_filter = ('is_read', 'created_at', 'media_type')
    search_fields = ('content', 'sender__username', 'conversation__participants__username')
    date_hierarchy = 'created_at'

@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'emoji', 'created_at')
    list_filter = ('created_at', 'emoji')
    search_fields = ('user__username', 'message__content')
    date_hierarchy = 'created_at'
