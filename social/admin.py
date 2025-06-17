from django.contrib import admin
from .models import Post, Comment, Like, Story, StoryView

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'content', 'created_at', 'is_private', 'likes_count', 'comments_count')
    list_filter = ('is_private', 'created_at')
    search_fields = ('content', 'author__username')
    date_hierarchy = 'created_at'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'content', 'created_at', 'likes_count')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'post__content')
    date_hierarchy = 'created_at'

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'comment', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'post__content', 'comment__content')
    date_hierarchy = 'created_at'

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('author', 'content_type', 'created_at', 'expires_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('author__username', 'caption')
    date_hierarchy = 'created_at'

@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ('story', 'viewer', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('story__author__username', 'viewer__username')
    date_hierarchy = 'viewed_at'
