import pytest
from django.utils import timezone
from messaging.models import Conversation, Message, MessageReaction
from users.tests.conftest import test_user, test_user2

@pytest.mark.django_db
class TestConversationModel:
    def test_create_conversation(self, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        assert conversation.participants.count() == 2
        assert test_user in conversation.participants.all()
        assert test_user2 in conversation.participants.all()
        assert conversation.created_at is not None
        assert conversation.updated_at is not None
        assert conversation.last_message is None

    def test_conversation_str(self, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        expected_str = f"Conversation entre {test_user.username}, {test_user2.username}"
        assert str(conversation) == expected_str

    def test_update_last_message(self, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user,
            content='Test message'
        )
        conversation.last_message = message
        conversation.save()
        
        assert conversation.last_message == message
        assert conversation.updated_at is not None

@pytest.mark.django_db
class TestMessageModel:
    def test_create_message(self, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user,
            content='Test message'
        )
        
        assert message.conversation == conversation
        assert message.sender == test_user
        assert message.content == 'Test message'
        assert not message.is_read
        assert message.read_at is None
        assert message.created_at is not None
        assert message.updated_at is not None

    def test_message_str(self, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user,
            content='Test message'
        )
        
        expected_str = f"Message de {test_user.username} dans {conversation}"
        assert str(message) == expected_str

    def test_mark_as_read(self, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user,
            content='Test message'
        )
        
        assert not message.is_read
        message.mark_as_read()
        assert message.is_read
        assert message.read_at is not None

@pytest.mark.django_db
class TestMessageReactionModel:
    def test_create_reaction(self, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user,
            content='Test message'
        )
        
        reaction = MessageReaction.objects.create(
            message=message,
            user=test_user2,
            emoji='👍'
        )
        
        assert reaction.message == message
        assert reaction.user == test_user2
        assert reaction.emoji == '👍'
        assert reaction.created_at is not None

    def test_reaction_str(self, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user,
            content='Test message'
        )
        
        reaction = MessageReaction.objects.create(
            message=message,
            user=test_user2,
            emoji='👍'
        )
        
        expected_str = f"{test_user2.username} a réagi avec 👍 à {message}"
        assert str(reaction) == expected_str

    def test_unique_reaction(self, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user,
            content='Test message'
        )
        
        MessageReaction.objects.create(
            message=message,
            user=test_user2,
            emoji='👍'
        )
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            MessageReaction.objects.create(
                message=message,
                user=test_user2,
                emoji='👍'
            ) 