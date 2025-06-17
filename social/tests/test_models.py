import pytest
from django.utils import timezone
from datetime import timedelta
from social.models import Post, Comment, Like, Story, StoryView
from users.tests.conftest import test_user, test_user2

@pytest.mark.django_db
class TestPostModel:
    def test_create_post(self, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post content',
            is_private=False
        )
        assert post.author == test_user
        assert post.content == 'Test post content'
        assert not post.is_private
        assert post.likes_count == 0
        assert post.comments_count == 0
        assert post.created_at is not None
        assert post.updated_at is not None

    def test_post_str(self, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post content'
        )
        assert str(post) == f"Post de {test_user.username} - {post.created_at}"

    def test_post_with_hashtags(self, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post with #hashtag1 and #hashtag2',
            hashtags=['hashtag1', 'hashtag2']
        )
        assert len(post.hashtags) == 2
        assert 'hashtag1' in post.hashtags
        assert 'hashtag2' in post.hashtags

    def test_post_with_mentions(self, test_user, test_user2):
        post = Post.objects.create(
            author=test_user,
            content='Test post mentioning @testuser2'
        )
        post.mentions.add(test_user2)
        assert post.mentions.count() == 1
        assert test_user2 in post.mentions.all()

@pytest.mark.django_db
class TestCommentModel:
    def test_create_comment(self, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        comment = Comment.objects.create(
            post=post,
            author=test_user,
            content='Test comment'
        )
        assert comment.post == post
        assert comment.author == test_user
        assert comment.content == 'Test comment'
        assert comment.likes_count == 0
        assert comment.parent is None
        assert comment.created_at is not None
        assert comment.updated_at is not None

    def test_comment_str(self, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        comment = Comment.objects.create(
            post=post,
            author=test_user,
            content='Test comment'
        )
        assert str(comment) == f"Commentaire de {test_user.username} sur {post}"

    def test_nested_comments(self, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        parent_comment = Comment.objects.create(
            post=post,
            author=test_user,
            content='Parent comment'
        )
        reply = Comment.objects.create(
            post=post,
            author=test_user,
            content='Reply comment',
            parent=parent_comment
        )
        assert reply.parent == parent_comment
        assert parent_comment.replies.count() == 1
        assert reply in parent_comment.replies.all()

@pytest.mark.django_db
class TestLikeModel:
    def test_like_post(self, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        like = Like.objects.create(
            user=test_user,
            post=post
        )
        assert like.user == test_user
        assert like.post == post
        assert like.comment is None
        assert like.created_at is not None

    def test_like_comment(self, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        comment = Comment.objects.create(
            post=post,
            author=test_user,
            content='Test comment'
        )
        like = Like.objects.create(
            user=test_user,
            comment=comment
        )
        assert like.user == test_user
        assert like.comment == comment
        assert like.post is None
        assert like.created_at is not None

    def test_unique_like(self, test_user):
        post = Post.objects.create(
            author=test_user,
            content='Test post'
        )
        Like.objects.create(user=test_user, post=post)
        with pytest.raises(Exception):  # Should raise IntegrityError
            Like.objects.create(user=test_user, post=post)

@pytest.mark.django_db
class TestStoryModel:
    def test_create_story(self, test_user):
        story = Story.objects.create(
            author=test_user,
            content='test_story.jpg',
            content_type='image',
            caption='Test story'
        )
        assert story.author == test_user
        assert story.content == 'test_story.jpg'
        assert story.content_type == 'image'
        assert story.caption == 'Test story'
        assert story.created_at is not None
        assert story.expires_at is not None
        assert story.expires_at > timezone.now()

    def test_story_str(self, test_user):
        story = Story.objects.create(
            author=test_user,
            content='test_story.jpg',
            content_type='image'
        )
        assert str(story) == f"Story de {test_user.username} - {story.created_at}"

    def test_story_with_mentions(self, test_user, test_user2):
        story = Story.objects.create(
            author=test_user,
            content='test_story.jpg',
            content_type='image'
        )
        story.mentions.add(test_user2)
        assert story.mentions.count() == 1
        assert test_user2 in story.mentions.all()

@pytest.mark.django_db
class TestStoryViewModel:
    def test_create_story_view(self, test_user, test_user2):
        story = Story.objects.create(
            author=test_user,
            content='test_story.jpg',
            content_type='image'
        )
        view = StoryView.objects.create(
            story=story,
            viewer=test_user2
        )
        assert view.story == story
        assert view.viewer == test_user2
        assert view.viewed_at is not None

    def test_unique_story_view(self, test_user, test_user2):
        story = Story.objects.create(
            author=test_user,
            content='test_story.jpg',
            content_type='image'
        )
        StoryView.objects.create(story=story, viewer=test_user2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            StoryView.objects.create(story=story, viewer=test_user2) 