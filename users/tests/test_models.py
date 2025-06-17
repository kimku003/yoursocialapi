import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from users.models import User, UserSettings

@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
        assert user.username == 'testuser'
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser
        assert user.is_active

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        assert admin.email == 'admin@example.com'
        assert admin.username == 'admin'
        assert admin.is_staff
        assert admin.is_superuser
        assert admin.is_active

    def test_user_str(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        assert str(user) == 'testuser'

    def test_get_full_name(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        assert user.get_full_name() == 'Test User'

    def test_get_full_name_no_names(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        assert user.get_full_name() == 'testuser'

@pytest.mark.django_db
class TestUserSettingsModel:
    def test_create_user_settings(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        settings = UserSettings.objects.create(user=user)
        assert settings.user == user
        assert settings.email_notifications is True
        assert settings.push_notifications is True
        assert settings.language == 'fr'
        assert settings.theme == 'light'

    def test_user_settings_str(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        settings = UserSettings.objects.create(user=user)
        assert str(settings) == 'Paramètres de testuser'

    def test_user_settings_unique_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        UserSettings.objects.create(user=user)
        with pytest.raises(Exception):  # Should raise IntegrityError
            UserSettings.objects.create(user=user) 