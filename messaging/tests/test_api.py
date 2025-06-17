import pytest
from django.urls import reverse
from rest_framework import status
from messaging.models import Conversation, Message, MessageReaction
from users.tests.conftest import authenticated_client, test_user, test_user2

@pytest.mark.django_db
class TestConversationAPI:
    def test_create_conversation(self, authenticated_client, test_user, test_user2):
        url = reverse('api:create_conversation')
        data = {
            'participants': [test_user2.id]
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Conversation.objects.count() == 1
        conversation = Conversation.objects.first()
        assert conversation.participants.count() == 2
        assert test_user in conversation.participants.all()
        assert test_user2 in conversation.participants.all()

    def test_list_conversations(self, authenticated_client, test_user, test_user2):
        # Create some conversations
        conv1 = Conversation.objects.create()
        conv1.participants.add(test_user, test_user2)
        
        conv2 = Conversation.objects.create()
        conv2.participants.add(test_user)
        
        url = reverse('api:list_conversations')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_get_conversation(self, authenticated_client, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        url = reverse('api:get_conversation', kwargs={'conversation_id': conversation.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == conversation.id
        assert len(response.data['participants']) == 2

@pytest.mark.django_db
class TestMessageAPI:
    def test_create_message(self, authenticated_client, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        url = reverse('api:create_message', kwargs={'conversation_id': conversation.id})
        data = {
            'content': 'Test message'
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == data['content']
        assert response.data['sender']['id'] == test_user.id
        assert Message.objects.count() == 1

    def test_list_messages(self, authenticated_client, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        Message.objects.create(
            conversation=conversation,
            sender=test_user,
            content='Message 1'
        )
        Message.objects.create(
            conversation=conversation,
            sender=test_user2,
            content='Message 2'
        )
        
        url = reverse('api:list_messages', kwargs={'conversation_id': conversation.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_mark_message_as_read(self, authenticated_client, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user2,
            content='Test message'
        )
        
        url = reverse('api:mark_message_read', kwargs={'message_id': message.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        message.refresh_from_db()
        assert message.is_read
        assert message.read_at is not None

@pytest.mark.django_db
class TestMessageReactionAPI:
    def test_add_reaction(self, authenticated_client, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user2,
            content='Test message'
        )
        
        url = reverse('api:add_reaction', kwargs={'message_id': message.id})
        data = {
            'emoji': '👍'
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert MessageReaction.objects.count() == 1
        reaction = MessageReaction.objects.first()
        assert reaction.emoji == '👍'
        assert reaction.user == test_user

    def test_remove_reaction(self, authenticated_client, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user2,
            content='Test message'
        )
        
        reaction = MessageReaction.objects.create(
            message=message,
            user=test_user,
            emoji='👍'
        )
        
        url = reverse('api:remove_reaction', kwargs={'reaction_id': reaction.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not MessageReaction.objects.filter(id=reaction.id).exists()

    def test_list_reactions(self, authenticated_client, test_user, test_user2):
        conversation = Conversation.objects.create()
        conversation.participants.add(test_user, test_user2)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=test_user2,
            content='Test message'
        )
        
        MessageReaction.objects.create(
            message=message,
            user=test_user,
            emoji='👍'
        )
        MessageReaction.objects.create(
            message=message,
            user=test_user2,
            emoji='❤️'
        )
        
        url = reverse('api:list_reactions', kwargs={'message_id': message.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2 