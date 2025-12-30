"""Integration tests for full API flow with mocked external APIs."""

import json
from unittest.mock import Mock

import pytest

from app import create_app


@pytest.fixture
def client():
    """Create a test client with reset state."""
    app = create_app(
        config_override={
            "PLATFORMS": {},
            "ACTIVE_PLATFORM": None,
            "API_KEY": None,
            "SERVER_PORT": 5000,
        }
    )
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client, app


class TestColorExtractionFlow:
    """Test complete flow: mention fetch → color parse → API response."""

    def test_mastodon_mention_with_hex_color(self, client):
        """Mastodon mention containing #FF0000 returns red color."""
        test_client, app = client
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "Set the color to #FF0000 please!",
                "id": "12345",
                "account": "testuser@mastodon.social",
                "created_at": "2024-01-15T10:30:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["color"]["hex"].upper() == "#FF0000"
        assert data["color"]["rgb"] == [255, 0, 0]
        assert data["mention"]["id"] == "12345"
        assert data["platform"] == "mastodon"

    def test_bluesky_mention_with_color_name(self, client):
        """Bluesky mention containing 'blue' returns blue color."""
        test_client, app = client
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "Make it blue!",
                "id": "at://did:plc:abc/post/123",
                "account": "testuser.bsky.social",
                "created_at": "2024-01-15T10:30:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"bluesky": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "bluesky"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["color"]["name"] == "blue"
        assert data["color"]["hex"].upper() == "#0000FF"
        assert data["platform"] == "bluesky"

    def test_color_priority_hex_over_name(self, client):
        """Hex color takes priority over color name in same mention."""
        test_client, app = client
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "I want green but actually #FF00FF",
                "id": "12345",
                "account": "testuser",
                "created_at": "2024-01-15T10:30:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        # Hex should take priority over color name
        assert data["color"]["hex"].upper() == "#FF00FF"

    def test_rgb_format_extraction(self, client):
        """RGB format (rgb(255, 128, 0)) is correctly extracted."""
        test_client, app = client
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "Use rgb(255, 128, 0) for orange",
                "id": "12345",
                "account": "testuser",
                "created_at": "2024-01-15T10:30:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["color"]["rgb"] == [255, 128, 0]

    def test_no_color_returns_white_default(self, client):
        """Mention without color info returns white default."""
        test_client, app = client
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "Hello, this is just a regular mention!",
                "id": "12345",
                "account": "testuser",
                "created_at": "2024-01-15T10:30:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["color"]["name"] == "white"
        assert data["color"]["hex"].upper() == "#FFFFFF"
        assert "message" in data

    def test_platform_switching(self, client):
        """Can switch between platforms via query param."""
        test_client, app = client
        mock_mastodon = Mock()
        mock_mastodon.get_latest_mentions.return_value = [
            {
                "text": "Mastodon says red",
                "id": "m123",
                "account": "user@mastodon",
                "created_at": "2024-01-15T10:30:00Z",
            }
        ]

        mock_bluesky = Mock()
        mock_bluesky.get_latest_mentions.return_value = [
            {
                "text": "Bluesky says blue",
                "id": "b123",
                "account": "user.bsky.social",
                "created_at": "2024-01-15T10:30:00Z",
            }
        ]

        app.config["PLATFORMS"] = {"mastodon": mock_mastodon, "bluesky": mock_bluesky}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        # Request from Mastodon
        response = test_client.get("/api/v1/color?platform=mastodon")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["color"]["name"] == "red"
        assert data["platform"] == "mastodon"

        # Request from Bluesky
        response = test_client.get("/api/v1/color?platform=bluesky")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["color"]["name"] == "blue"
        assert data["platform"] == "bluesky"

    def test_multiple_mentions_first_color_wins(self, client):
        """When multiple mentions exist, first one with color is used."""
        test_client, app = client
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "No color here",
                "id": "1",
                "account": "user1",
                "created_at": "2024-01-15T10:30:00Z",
            },
            {
                "text": "Make it purple!",
                "id": "2",
                "account": "user2",
                "created_at": "2024-01-15T10:29:00Z",
            },
            {
                "text": "I want yellow",
                "id": "3",
                "account": "user3",
                "created_at": "2024-01-15T10:28:00Z",
            },
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        # Should get purple from second mention (first with color)
        assert data["color"]["name"] == "purple"
        assert data["mention"]["id"] == "2"


class TestMentionsFlow:
    """Test mentions endpoint full flow."""

    def test_mastodon_mentions_strips_html(self, client):
        """HTML tags are stripped from Mastodon content."""
        test_client, app = client
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "<p>Hello <strong>world</strong>!</p>",
                "id": "12345",
                "account": "testuser",
                "created_at": "2024-01-15T10:30:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/mentions")

        assert response.status_code == 200
        data = json.loads(response.data)
        # HTML should be stripped
        assert data["mentions"][0]["text"] == "Hello world!"

    def test_mentions_respects_limit(self, client):
        """Limit parameter is passed to platform."""
        test_client, app = client
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = []
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/mentions?limit=5")

        assert response.status_code == 200
        mock_platform.get_latest_mentions.assert_called_once_with(limit=5)

    def test_mentions_returns_count(self, client):
        """Response includes count of mentions."""
        test_client, app = client
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {"text": "One", "id": "1", "account": "a", "created_at": "2024-01-01"},
            {"text": "Two", "id": "2", "account": "b", "created_at": "2024-01-01"},
            {"text": "Three", "id": "3", "account": "c", "created_at": "2024-01-01"},
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/mentions")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["count"] == 3
        assert len(data["mentions"]) == 3


class TestPlatformInitialization:
    """Test platform initialization flow."""

    def test_multiple_platforms_available(self, client):
        """Multiple platforms can be configured and listed."""
        test_client, app = client
        mock_mastodon = Mock()
        mock_bluesky = Mock()
        app.config["PLATFORMS"] = {"mastodon": mock_mastodon, "bluesky": mock_bluesky}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/platforms")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "mastodon" in data["available_platforms"]
        assert "bluesky" in data["available_platforms"]
        assert data["active_platform"] == "mastodon"

    def test_no_platforms_configured(self, client):
        """Graceful handling when no platforms are configured."""
        test_client, app = client
        app.config["PLATFORMS"] = {}
        app.config["ACTIVE_PLATFORM"] = None

        response = test_client.get("/api/v1/color")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestAuthenticationFlow:
    """Test API authentication flow."""

    def test_auth_required_when_key_configured(self, client):
        """API key is required when configured."""
        test_client, app = client
        app.config["API_KEY"] = "secret-key"
        app.config["PLATFORMS"] = {"mastodon": Mock()}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        # Without key
        response = test_client.get("/api/v1/color")
        assert response.status_code == 401

        # With wrong key
        response = test_client.get("/api/v1/color", headers={"X-API-Key": "wrong"})
        assert response.status_code == 401

        # With correct key
        app.config["PLATFORMS"]["mastodon"].get_latest_mentions.return_value = []
        response = test_client.get("/api/v1/color", headers={"X-API-Key": "secret-key"})
        assert response.status_code == 200

    def test_auth_bypassed_when_no_key_configured(self, client):
        """Authentication is bypassed when no API key is configured."""
        test_client, app = client
        app.config["API_KEY"] = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = []
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
