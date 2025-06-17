from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserSettings

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_private', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_private', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    date_hierarchy = 'date_joined'
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('email', 'first_name', 'last_name', 'bio', 'avatar', 'banner', 'date_of_birth', 'location', 'website')
        }),
        (_('Paramètres du compte'), {
            'fields': ('is_private', 'followers_count', 'following_count', 'posts_count')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Dates importantes'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'push_notifications', 'language', 'theme', 'updated_at')
    list_filter = ('email_notifications', 'push_notifications', 'language', 'theme')
    search_fields = ('user__username',)
    date_hierarchy = 'updated_at'
