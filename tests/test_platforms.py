"""Tests for platform integrations."""

import pytest
from unittest.mock import Mock, patch
from platforms.base import SocialPlatform
from platforms.mastodon import MastodonPlatform
from platforms.bluesky import BlueskyPlatform


class TestMastodonPlatform:
    """Tests for Mastodon platform integration."""

    def test_initialize_success(self):
        """Test successful Mastodon initialization."""
        platform = MastodonPlatform()
        config = {
            "instance_url": "https://mastodon.social",
            "access_token": "test_token",
        }

        with patch("platforms.mastodon.Mastodon") as mock_mastodon:
            mock_client = Mock()
            mock_client.account_verify_credentials.return_value = {"id": 1}
            mock_mastodon.return_value = mock_client

            result = platform.initialize(config)

            assert result is True
            assert platform.client is not None
            mock_mastodon.assert_called_once_with(
                access_token="test_token", api_base_url="https://mastodon.social"
            )

    def test_initialize_missing_config(self):
        """Test initialization with missing config."""
        platform = MastodonPlatform()
        config = {}

        result = platform.initialize(config)

        assert result is False
        assert platform.client is None

    def test_initialize_invalid_credentials(self):
        """Test initialization with invalid credentials."""
        platform = MastodonPlatform()
        config = {
            "instance_url": "https://mastodon.social",
            "access_token": "invalid_token",
        }

        with patch("platforms.mastodon.Mastodon") as mock_mastodon:
            mock_client = Mock()
            mock_client.account_verify_credentials.side_effect = Exception(
                "Invalid token"
            )
            mock_mastodon.return_value = mock_client

            result = platform.initialize(config)

            assert result is False

    def test_get_latest_mentions_success(self):
        """Test getting mentions successfully."""
        platform = MastodonPlatform()
        platform.client = Mock()

        mock_notifications = [
            {
                "type": "mention",
                "status": {
                    "content": "<p>Make it red!</p>",
                    "id": "123",
                    "created_at": "2024-01-01T00:00:00Z",
                    "account": {"username": "testuser"},
                },
            },
            {"type": "like", "status": {"content": "Not a mention"}},
        ]
        platform.client.notifications.return_value = mock_notifications

        result = platform.get_latest_mentions(limit=10)

        assert len(result) == 1
        assert result[0]["text"] == "<p>Make it red!</p>"
        assert result[0]["id"] == "123"
        assert result[0]["account"] == "testuser"

    def test_get_latest_mentions_no_client(self):
        """Test getting mentions without initialized client."""
        platform = MastodonPlatform()
        platform.client = None

        result = platform.get_latest_mentions()

        assert result == []

    def test_get_latest_mentions_error(self):
        """Test error handling when fetching mentions."""
        platform = MastodonPlatform()
        platform.client = Mock()
        platform.client.notifications.side_effect = Exception("API Error")

        result = platform.get_latest_mentions()

        assert result == []


class TestBlueskyPlatform:
    """Tests for Bluesky platform integration."""

    def test_initialize_success(self):
        """Test successful Bluesky initialization."""
        platform = BlueskyPlatform()
        config = {
            "identifier": "test@example.com",
            "password": "test_password",
            "debug": "false",
        }

        with patch("platforms.bluesky.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            result = platform.initialize(config)

            assert result is True
            assert platform.client is not None
            assert platform.debug is False
            mock_client.login.assert_called_once_with(
                login="test@example.com", password="test_password"
            )

    def test_initialize_with_debug(self):
        """Test initialization with debug enabled."""
        platform = BlueskyPlatform()
        config = {
            "identifier": "test@example.com",
            "password": "test_password",
            "debug": "true",
        }

        with patch("platforms.bluesky.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            result = platform.initialize(config)

            assert result is True
            assert platform.debug is True

    def test_initialize_missing_config(self):
        """Test initialization with missing config."""
        platform = BlueskyPlatform()
        config = {}

        result = platform.initialize(config)

        assert result is False
        assert platform.client is None

    def test_initialize_invalid_credentials(self):
        """Test initialization with invalid credentials."""
        platform = BlueskyPlatform()
        config = {"identifier": "test@example.com", "password": "wrong_password"}

        with patch("platforms.bluesky.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.login.side_effect = Exception("Invalid credentials")
            mock_client_class.return_value = mock_client

            result = platform.initialize(config)

            assert result is False

    def test_get_latest_mentions_success(self):
        """Test getting mentions successfully."""
        platform = BlueskyPlatform()
        platform.client = Mock()
        platform.debug = False

        # Mock notification response
        mock_notification = Mock()
        mock_notification.reason = "reply"
        mock_notification.uri = "at://did:plc:test/app.bsky.feed.post/123"
        mock_notification.indexed_at = "2024-01-01T00:00:00Z"
        mock_notification.author = Mock()
        mock_notification.author.handle = "testuser"
        mock_notification.record = None

        mock_notifications_response = Mock()
        mock_notifications_response.notifications = [mock_notification]

        platform.client.app.bsky.notification.list_notifications.return_value = (
            mock_notifications_response
        )

        # Mock post fetch
        mock_post = Mock()
        mock_post.record = Mock()
        mock_post.record.text = "Make it red!"
        mock_post.author = Mock()
        mock_post.author.handle = "testuser"

        mock_posts_response = Mock()
        mock_posts_response.posts = [mock_post]

        platform.client.app.bsky.feed.get_posts.return_value = mock_posts_response

        # Mock params
        with patch(
            "platforms.bluesky.models.AppBskyNotificationListNotifications.Params"
        ):
            result = platform.get_latest_mentions(limit=10)

        assert len(result) == 1
        assert result[0]["text"] == "Make it red!"
        assert result[0]["account"] == "testuser"

    def test_get_latest_mentions_no_client(self):
        """Test getting mentions without initialized client."""
        platform = BlueskyPlatform()
        platform.client = None

        result = platform.get_latest_mentions()

        assert result == []

    def test_get_latest_mentions_filter_mentions_only(self):
        """Test that only mentions and replies are processed."""
        platform = BlueskyPlatform()
        platform.client = Mock()
        platform.debug = False

        # Create notifications with different reasons
        mock_like = Mock()
        mock_like.reason = "like"

        mock_reply = Mock()
        mock_reply.reason = "reply"
        mock_reply.uri = "at://did:plc:test/app.bsky.feed.post/123"
        mock_reply.indexed_at = "2024-01-01T00:00:00Z"
        mock_reply.author = Mock()
        mock_reply.author.handle = "testuser"
        mock_reply.record = None

        mock_notifications_response = Mock()
        mock_notifications_response.notifications = [mock_like, mock_reply]

        platform.client.app.bsky.notification.list_notifications.return_value = (
            mock_notifications_response
        )

        # Mock post fetch
        mock_post = Mock()
        mock_post.record = Mock()
        mock_post.record.text = "Test mention"
        mock_post.author = Mock()
        mock_post.author.handle = "testuser"

        mock_posts_response = Mock()
        mock_posts_response.posts = [mock_post]

        platform.client.app.bsky.feed.get_posts.return_value = mock_posts_response

        with patch(
            "platforms.bluesky.models.AppBskyNotificationListNotifications.Params"
        ):
            result = platform.get_latest_mentions(limit=10)

        # Should only process the reply, not the like
        assert len(result) == 1

    def test_get_latest_mentions_error(self):
        """Test error handling when fetching mentions."""
        platform = BlueskyPlatform()
        platform.client = Mock()
        platform.debug = False
        platform.client.app.bsky.notification.list_notifications.side_effect = (
            Exception("API Error")
        )

        with patch(
            "platforms.bluesky.models.AppBskyNotificationListNotifications.Params"
        ):
            result = platform.get_latest_mentions()

        assert result == []


class TestSocialPlatformBase:
    """Tests for base SocialPlatform class."""

    def test_base_class_is_abstract(self):
        """Test that SocialPlatform is abstract."""
        with pytest.raises(TypeError):
            # Cannot instantiate abstract class
            SocialPlatform()
