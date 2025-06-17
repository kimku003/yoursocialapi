import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User, UserSettings

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user():
    return User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='testpass123'
    )

@pytest.fixture
def test_user2():
    return User.objects.create_user(
        email='test2@example.com',
        username='testuser2',
        password='testpass123'
    )

@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client

@pytest.mark.django_db
class TestUserRegistration:
    def test_register_user_success(self, api_client):
        url = reverse('api:register')
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
        
        user = User.objects.get(email='newuser@example.com')
        assert user.username == 'newuser'
        assert user.first_name == 'New'
        assert user.last_name == 'User'
        assert UserSettings.objects.filter(user=user).exists()

    def test_register_user_invalid_data(self, api_client):
        url = reverse('api:register')
        data = {
            'email': 'invalid-email',
            'username': 'newuser',
            'password': '123'  # Too short
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestUserLogin:
    def test_login_success(self, api_client, test_user):
        url = reverse('api:login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data

    def test_login_invalid_credentials(self, api_client):
        url = reverse('api:login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestUserProfile:
    def test_get_profile(self, authenticated_client, test_user):
        url = reverse('api:me')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == test_user.email
        assert response.data['username'] == test_user.username

    def test_update_profile(self, authenticated_client, test_user):
        url = reverse('api:me')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'bio': 'New bio',
            'location': 'Paris'
        }
        response = authenticated_client.put(url, data)
        assert response.status_code == status.HTTP_200_OK
        test_user.refresh_from_db()
        assert test_user.first_name == 'Updated'
        assert test_user.last_name == 'Name'
        assert test_user.bio == 'New bio'
        assert test_user.location == 'Paris'

@pytest.mark.django_db
class TestUserFollow:
    def test_follow_user(self, authenticated_client, test_user, test_user2):
        url = reverse('api:follow_user', kwargs={'user_id': test_user2.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['action'] == 'followed'
        assert test_user.following.filter(id=test_user2.id).exists()

    def test_unfollow_user(self, authenticated_client, test_user, test_user2):
        # First follow
        test_user.following.add(test_user2)
        # Then unfollow
        url = reverse('api:follow_user', kwargs={'user_id': test_user2.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['action'] == 'unfollowed'
        assert not test_user.following.filter(id=test_user2.id).exists()

    def test_follow_self(self, authenticated_client, test_user):
        url = reverse('api:follow_user', kwargs={'user_id': test_user.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'Vous ne pouvez pas vous suivre vous-même' 