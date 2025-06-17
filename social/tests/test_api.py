import pytest
from django.urls import reverse
from rest_framework import status
from social.models import Post, Comment, Like, Story, StoryView
from users.tests.conftest import authenticated_client, test_user, test_user2

@pytest.mark.django_db
class TestPostAPI:
    def test_create_post(self, authenticated_client, test_user):
        url = reverse('api:create_post')
        data = {
            'content': 'Test post content',
            'is_private': False,
            'hashtags': ['test', 'post'],
            'mentions': []
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == data['content']
        assert response.data['author']['id'] == test_user.id
        assert Post.objects.count() == 1

    def test_list_posts(self, authenticated_client, test_user):
        # Create some posts
        Post.objects.create(author=test_user, content='Post 1')
        Post.objects.create(author=test_user, content='Post 2')
        
        url = reverse('api:list_posts')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_get_post(self, authenticated_client, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        url = reverse('api:get_post', kwargs={'post_id': post.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == post.id
        assert response.data['content'] == post.content

    def test_delete_post(self, authenticated_client, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        url = reverse('api:delete_post', kwargs={'post_id': post.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert not Post.objects.filter(id=post.id).exists()

    def test_delete_other_user_post(self, authenticated_client, test_user2):
        post = Post.objects.create(
            author=test_user2,
            content='Test post'
        )
        url = reverse('api:delete_post', kwargs={'post_id': post.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Post.objects.filter(id=post.id).exists()

@pytest.mark.django_db
class TestCommentAPI:
    def test_create_comment(self, authenticated_client, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        url = reverse('api:create_comment', kwargs={'post_id': post.id})
        data = {
            'content': 'Test comment'
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == data['content']
        assert response.data['post_id'] == post.id
        assert Comment.objects.count() == 1

    def test_list_comments(self, authenticated_client, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        Comment.objects.create(
            post=post,
            author=test_user,
            content='Comment 1'
        )
        Comment.objects.create(
            post=post,
            author=test_user,
            content='Comment 2'
        )
        
        url = reverse('api:list_comments', kwargs={'post_id': post.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

@pytest.mark.django_db
class TestLikeAPI:
    def test_like_post(self, authenticated_client, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        url = reverse('api:like_post', kwargs={'post_id': post.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['action'] == 'liked'
        assert Like.objects.filter(post=post, user=test_user).exists()

    def test_unlike_post(self, authenticated_client, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        Like.objects.create(post=post, user=test_user)
        url = reverse('api:like_post', kwargs={'post_id': post.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['action'] == 'unliked'
        assert not Like.objects.filter(post=post, user=test_user).exists()

    def test_like_comment(self, authenticated_client, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        comment = Comment.objects.create(
            post=post,
            author=test_user,
            content='Test comment'
        )
        url = reverse('api:like_comment', kwargs={'comment_id': comment.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['action'] == 'liked'
        assert Like.objects.filter(comment=comment, user=test_user).exists()

@pytest.mark.django_db
class TestStoryAPI:
    def test_create_story(self, authenticated_client, test_user):
        url = reverse('api:create_story')
        data = {
            'content': 'test_story.jpg',
            'content_type': 'image',
            'caption': 'Test story'
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content_type'] == data['content_type']
        assert response.data['caption'] == data['caption']
        assert Story.objects.count() == 1

    def test_list_stories(self, authenticated_client, test_user):
        Story.objects.create(
            author=test_user,
            content='test_story1.jpg',
            content_type='image'
        )
        Story.objects.create(
            author=test_user,
            content='test_story2.jpg',
            content_type='image'
        )
        
        url = reverse('api:list_stories')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_view_story(self, authenticated_client, test_user, test_user2):
        story = Story.objects.create(
            author=test_user,
            content='test_story.jpg',
            content_type='image'
        )
        url = reverse('api:view_story', kwargs={'story_id': story.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert StoryView.objects.filter(story=story, viewer=test_user2).exists()

    def test_list_story_views(self, authenticated_client, test_user):
        story = Story.objects.create(
            author=test_user,
            content='test_story.jpg',
            content_type='image'
        )
        StoryView.objects.create(story=story, viewer=test_user)
        
        url = reverse('api:list_story_views', kwargs={'story_id': story.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1 