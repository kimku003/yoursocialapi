import pytest
from django.utils import timezone
from notifications.models import Notification, NotificationPreference
from users.models import User
from social.models import Post, Comment, Like
from messaging.models import Message

@pytest.mark.django_db
class TestNotificationModel:
    def test_create_notification(self, test_user, test_user2):
        notification = Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='follow',
            content='Test notification'
        )
        assert notification.recipient == test_user
        assert notification.sender == test_user2
        assert notification.notification_type == 'follow'
        assert notification.content == 'Test notification'
        assert not notification.is_read
        assert notification.created_at is not None

    def test_notification_string_representation(self, test_user, test_user2):
        notification = Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='follow',
            content='Test notification'
        )
        expected_str = f"Notification pour {test_user.username} de {test_user2.username} (follow)"
        assert str(notification) == expected_str

    def test_mark_notification_as_read(self, test_user, test_user2):
        notification = Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='follow',
            content='Test notification'
        )
        assert not notification.is_read
        notification.mark_as_read()
        assert notification.is_read
        assert notification.read_at is not None

    def test_create_notification_with_post(self, test_user, test_user2):
        post = Post.objects.create(
            author=test_user2,
            content='Test post'
        )
        notification = Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='post_mention',
            content='Test notification',
            post=post
        )
        assert notification.post == post
        assert notification.notification_type == 'post_mention'

    def test_create_notification_with_comment(self, test_user, test_user2):
        post = Post.objects.create(
            author=test_user2,
            content='Test post'
        )
        comment = Comment.objects.create(
            post=post,
            author=test_user2,
            content='Test comment'
        )
        notification = Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='comment',
            content='Test notification',
            comment=comment
        )
        assert notification.comment == comment
        assert notification.notification_type == 'comment'

    def test_create_notification_with_message(self, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user2,
            content='Test message'
        )
        notification = Notification.objects.create(
            recipient=test_user,
            sender=test_user2,
            notification_type='message',
            content='Test notification',
            message=message
        )
        assert notification.message == message
        assert notification.notification_type == 'message'

@pytest.mark.django_db
class TestNotificationPreferenceModel:
    def test_create_notification_preference(self, test_user):
        preference = NotificationPreference.objects.create(
            user=test_user,
            email_notifications=True,
            push_notifications=False,
            follow_notifications=True,
            post_mention_notifications=True,
            comment_notifications=True,
            like_notifications=False,
            message_notifications=True
        )
        assert preference.user == test_user
        assert preference.email_notifications
        assert not preference.push_notifications
        assert preference.follow_notifications
        assert preference.post_mention_notifications
        assert preference.comment_notifications
        assert not preference.like_notifications
        assert preference.message_notifications

    def test_notification_preference_string_representation(self, test_user):
        preference = NotificationPreference.objects.create(
            user=test_user,
            email_notifications=True
        )
        expected_str = f"Préférences de notification pour {test_user.username}"
        assert str(preference) == expected_str

    def test_notification_preference_default_values(self, test_user):
        preference = NotificationPreference.objects.create(user=test_user)
        assert preference.email_notifications
        assert preference.push_notifications
        assert preference.follow_notifications
        assert preference.post_mention_notifications
        assert preference.comment_notifications
        assert preference.like_notifications
        assert preference.message_notifications 