"""Tests for Flask application and API endpoints."""

import pytest
import json
from unittest.mock import Mock, patch
import app


@pytest.fixture
def client():
    """Create a test client."""
    app.app.config["TESTING"] = True
    # Reset global state
    app.platforms = {}
    app.active_platform = None
    app.api_key = None
    app.server_port = 5000
    with app.app.test_client() as client:
        yield client


@pytest.fixture
def mock_config():
    """Create a mock config."""
    config = {
        "server": {"api_key": "test-api-key", "port": "8080"},
        "mastodon": {
            "instance_url": "https://mastodon.social",
            "access_token": "test_token",
        },
    }
    return config


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint_no_auth(self, client):
        """Test root endpoint doesn't require authentication."""
        response = client.get("/")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data
        assert "version" in data
        assert "available_platforms" in data


class TestAuthentication:
    """Tests for API authentication."""

    def test_color_endpoint_without_api_key(self, client):
        """Test color endpoint without API key when auth is disabled."""
        app.api_key = None
        app.platforms = {}
        response = client.get("/api/v1/color")
        # Should work if no API key is configured
        assert response.status_code in [200, 400]  # 400 if no platforms

    def test_color_endpoint_with_valid_key(self, client):
        """Test color endpoint with valid API key."""
        app.api_key = "test-key"
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = []
        app.platforms = {"mastodon": mock_platform}
        app.active_platform = "mastodon"

        response = client.get("/api/v1/color", headers={"X-API-Key": "test-key"})

        assert response.status_code == 200

    def test_color_endpoint_with_invalid_key(self, client):
        """Test color endpoint with invalid API key."""
        app.api_key = "test-key"
        response = client.get("/api/v1/color", headers={"X-API-Key": "wrong-key"})

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Unauthorized"

    def test_color_endpoint_without_header(self, client):
        """Test color endpoint without API key header."""
        app.api_key = "test-key"
        response = client.get("/api/v1/color")

        assert response.status_code == 401


class TestColorEndpoint:
    """Tests for /api/v1/color endpoint."""

    def test_color_endpoint_with_mention(self, client):
        """Test color endpoint with a mention containing a color."""
        app.api_key = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "Make it red!",
                "id": "123",
                "account": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        app.platforms = {"mastodon": mock_platform}
        app.active_platform = "mastodon"

        response = client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "color" in data
        assert data["color"]["name"] == "red"
        assert "mention" in data

    def test_color_endpoint_no_color_found(self, client):
        """Test color endpoint when no color is found."""
        app.api_key = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "This is just text",
                "id": "123",
                "account": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        app.platforms = {"mastodon": mock_platform}
        app.active_platform = "mastodon"

        response = client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "color" in data
        assert data["color"]["name"] == "white"  # Default color
        assert "message" in data

    def test_color_endpoint_platform_parameter(self, client):
        """Test color endpoint with platform parameter."""
        app.api_key = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = []
        app.platforms = {"bluesky": mock_platform}

        response = client.get("/api/v1/color?platform=bluesky")

        assert response.status_code == 200
        mock_platform.get_latest_mentions.assert_called_once()

    def test_color_endpoint_invalid_platform(self, client):
        """Test color endpoint with invalid platform."""
        app.api_key = None
        app.platforms = {}
        response = client.get("/api/v1/color?platform=invalid")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestMentionsEndpoint:
    """Tests for /api/v1/mentions endpoint."""

    def test_mentions_endpoint_success(self, client):
        """Test mentions endpoint successfully returns mentions."""
        app.api_key = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "<p>Test mention</p>",
                "id": "123",
                "account": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        app.platforms = {"mastodon": mock_platform}
        app.active_platform = "mastodon"

        response = client.get("/api/v1/mentions")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "mentions" in data
        assert len(data["mentions"]) == 1
        assert data["mentions"][0]["text"] == "Test mention"  # HTML stripped
        assert "count" in data

    def test_mentions_endpoint_limit_parameter(self, client):
        """Test mentions endpoint with limit parameter."""
        app.api_key = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = []
        app.platforms = {"mastodon": mock_platform}
        app.active_platform = "mastodon"

        response = client.get("/api/v1/mentions?limit=5")

        assert response.status_code == 200
        mock_platform.get_latest_mentions.assert_called_once_with(limit=5)


class TestPlatformsEndpoint:
    """Tests for /api/v1/platforms endpoint."""

    def test_platforms_endpoint(self, client):
        """Test platforms endpoint."""
        app.api_key = None
        app.platforms = {"mastodon": Mock(), "bluesky": Mock()}
        app.active_platform = "mastodon"

        response = client.get("/api/v1/platforms")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "available_platforms" in data
        assert "active_platform" in data
        assert "mastodon" in data["available_platforms"]


class TestConfiguration:
    """Tests for configuration loading."""

    def test_load_api_key_from_config(self, mock_config):
        """Test loading API key from config."""
        with patch("app.load_config") as mock_load:
            mock_load.return_value = mock_config
            app.api_key = None
            app.load_api_key()
            assert app.api_key == "test-api-key"

    def test_load_api_key_missing(self):
        """Test loading API key when missing."""
        with patch("app.load_config") as mock_load:
            mock_load.return_value = {}
            app.api_key = None
            app.load_api_key()
            # Should not raise error, just log warning

    def test_load_server_config(self, mock_config):
        """Test loading server configuration."""
        with patch("app.load_config") as mock_load:
            mock_load.return_value = mock_config
            app.server_port = 5000
            app.load_server_config()
            assert app.server_port == 8080

    def test_load_server_config_invalid_port(self):
        """Test loading server config with invalid port."""
        config = {"server": {"port": "invalid"}}
        with patch("app.load_config") as mock_load:
            mock_load.return_value = config
            app.server_port = 5000
            app.load_server_config()
            # Should default to 5000 on invalid port
            assert app.server_port == 5000
