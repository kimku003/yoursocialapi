import pytest
from django.urls import reverse
from rest_framework import status
from notifications.models import Notification, NotificationPreference
from users.tests.conftest import authenticated_client, test_user, test_user2

@pytest.mark.django_db
class TestNotificationAPI:
    def test_list_notifications(self, authenticated_client, test_user, test_user2):
        # Créer quelques notifications
        Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='follow',
            content='Test notification 1'
        )
        Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='post_mention',
            content='Test notification 2'
        )
        
        url = reverse('api:list_notifications')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_mark_notification_as_read(self, authenticated_client, test_user, test_user2):
        notification = Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='follow',
            content='Test notification'
        )
        
        url = reverse('api:mark_notification_read', kwargs={'notification_id': notification.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read
        assert notification.read_at is not None

    def test_mark_all_notifications_as_read(self, authenticated_client, test_user, test_user2):
        # Créer plusieurs notifications non lues
        Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='follow',
            content='Test notification 1'
        )
        Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='post_mention',
            content='Test notification 2'
        )
        
        url = reverse('api:mark_all_notifications_read')
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Vérifier que toutes les notifications sont marquées comme lues
        notifications = Notification.objects.filter(recipient=test_user)
        assert all(notification.is_read for notification in notifications)

    def test_delete_notification(self, authenticated_client, test_user, test_user2):
        notification = Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='follow',
            content='Test notification'
        )
        
        url = reverse('api:delete_notification', kwargs={'notification_id': notification.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Notification.objects.filter(id=notification.id).exists()

@pytest.mark.django_db
class TestNotificationPreferenceAPI:
    def test_get_notification_preferences(self, authenticated_client, test_user):
        NotificationPreference.objects.create(
            user=test_user,
            email_notifications=True,
            push_notifications=False
        )
        
        url = reverse('api:get_notification_preferences')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email_notifications']
        assert not response.data['push_notifications']

    def test_update_notification_preferences(self, authenticated_client, test_user):
        NotificationPreference.objects.create(user=test_user)
        
        url = reverse('api:update_notification_preferences')
        data = {
            'email_notifications': False,
            'push_notifications': True,
            'follow_notifications': False,
            'post_mention_notifications': True,
            'comment_notifications': False,
            'like_notifications': True,
            'message_notifications': False
        }
        response = authenticated_client.put(url, data)
        assert response.status_code == status.HTTP_200_OK
        
        preferences = NotificationPreference.objects.get(user=test_user)
        assert not preferences.email_notifications
        assert preferences.push_notifications
        assert not preferences.follow_notifications
        assert preferences.post_mention_notifications
        assert not preferences.comment_notifications
        assert preferences.like_notifications
        assert not preferences.message_notifications

    def test_create_notification_preferences(self, authenticated_client, test_user):
        url = reverse('api:update_notification_preferences')
        data = {
            'email_notifications': True,
            'push_notifications': False,
            'follow_notifications': True,
            'post_mention_notifications': False,
            'comment_notifications': True,
            'like_notifications': False,
            'message_notifications': True
        }
        response = authenticated_client.put(url, data)
        assert response.status_code == status.HTTP_200_OK
        
        preferences = NotificationPreference.objects.get(user=test_user)
        assert preferences.email_notifications
        assert not preferences.push_notifications
        assert preferences.follow_notifications
        assert not preferences.post_mention_notifications
        assert preferences.comment_notifications
        assert not preferences.like_notifications
        assert preferences.message_notifications 