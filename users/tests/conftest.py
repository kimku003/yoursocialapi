import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from users.models import UserSettings

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(db):
    user = User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    UserSettings.objects.create(user=user)
    return user

@pytest.fixture
def test_user2(db):
    user = User.objects.create_user(
        email='test2@example.com',
        username='testuser2',
        password='testpass123',
        first_name='Test2',
        last_name='User2'
    )
    UserSettings.objects.create(user=user)
    return user

@pytest.fixture
def admin_user(db):
    user = User.objects.create_superuser(
        email='admin@example.com',
        username='admin',
        password='adminpass123'
    )
    UserSettings.objects.create(user=user)
    return user

@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client 