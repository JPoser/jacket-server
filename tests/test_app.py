"""Tests for Flask application and API endpoints."""

import pytest
import json
from unittest.mock import Mock, patch
from app import create_app


@pytest.fixture
def client():
    """Create a test client with no platforms configured."""
    app = create_app(
        config_override={
            "PLATFORMS": {},
            "ACTIVE_PLATFORM": None,
            "API_KEY": None,
            "SERVER_PORT": 5000,
        }
    )
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client, app


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
        test_client, _ = client
        response = test_client.get("/")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data
        assert "version" in data
        assert "available_platforms" in data


class TestAuthentication:
    """Tests for API authentication."""

    def test_color_endpoint_without_api_key(self, client):
        """Test color endpoint without API key when auth is disabled."""
        test_client, app = client
        app.config["API_KEY"] = None
        app.config["PLATFORMS"] = {}
        response = test_client.get("/api/v1/color")
        # Should work if no API key is configured
        assert response.status_code in [200, 400]  # 400 if no platforms

    def test_color_endpoint_with_valid_key(self, client):
        """Test color endpoint with valid API key."""
        test_client, app = client
        app.config["API_KEY"] = "test-key"
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = []
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color", headers={"X-API-Key": "test-key"})

        assert response.status_code == 200

    def test_color_endpoint_with_invalid_key(self, client):
        """Test color endpoint with invalid API key."""
        test_client, app = client
        app.config["API_KEY"] = "test-key"
        response = test_client.get("/api/v1/color", headers={"X-API-Key": "wrong-key"})

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Unauthorized"

    def test_color_endpoint_without_header(self, client):
        """Test color endpoint without API key header."""
        test_client, app = client
        app.config["API_KEY"] = "test-key"
        response = test_client.get("/api/v1/color")

        assert response.status_code == 401


class TestColorEndpoint:
    """Tests for /api/v1/color endpoint."""

    def test_color_endpoint_with_mention(self, client):
        """Test color endpoint with a mention containing a color."""
        test_client, app = client
        app.config["API_KEY"] = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "Make it red!",
                "id": "123",
                "account": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "color" in data
        assert data["color"]["name"] == "red"
        assert "mention" in data
        assert "effect" in data
        assert data["effect"] is None  # No effect in this mention

    def test_color_endpoint_with_effect(self, client):
        """Test color endpoint with a mention containing both color and effect."""
        test_client, app = client
        app.config["API_KEY"] = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "fade to red!",
                "id": "123",
                "account": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "color" in data
        assert data["color"]["name"] == "red"
        assert "effect" in data
        assert data["effect"] == "fade"

    def test_color_endpoint_with_underscore_effect(self, client):
        """Test color endpoint with effect containing underscore."""
        test_client, app = client
        app.config["API_KEY"] = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "wipe_down to blue!",
                "id": "123",
                "account": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["effect"] == "wipe_down"

    def test_color_endpoint_with_space_effect(self, client):
        """Test color endpoint with effect containing space instead of underscore."""
        test_client, app = client
        app.config["API_KEY"] = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "colour spiral to green!",
                "id": "123",
                "account": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["effect"] == "colour_spiral"

    def test_color_endpoint_no_color_found(self, client):
        """Test color endpoint when no color is found."""
        test_client, app = client
        app.config["API_KEY"] = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "This is just text",
                "id": "123",
                "account": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "color" in data
        assert data["color"]["name"] == "white"  # Default color
        assert "effect" in data
        assert data["effect"] is None
        assert "message" in data

    def test_color_endpoint_no_mentions(self, client):
        """Test color endpoint when no mentions are found."""
        test_client, app = client
        app.config["API_KEY"] = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = []
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/color")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "color" in data
        assert data["color"]["name"] == "white"
        assert "effect" in data
        assert data["effect"] is None

    def test_color_endpoint_platform_parameter(self, client):
        """Test color endpoint with platform parameter."""
        test_client, app = client
        app.config["API_KEY"] = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = []
        app.config["PLATFORMS"] = {"bluesky": mock_platform}

        response = test_client.get("/api/v1/color?platform=bluesky")

        assert response.status_code == 200
        mock_platform.get_latest_mentions.assert_called_once()

    def test_color_endpoint_invalid_platform(self, client):
        """Test color endpoint with invalid platform."""
        test_client, app = client
        app.config["API_KEY"] = None
        app.config["PLATFORMS"] = {}
        response = test_client.get("/api/v1/color?platform=invalid")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestMentionsEndpoint:
    """Tests for /api/v1/mentions endpoint."""

    def test_mentions_endpoint_success(self, client):
        """Test mentions endpoint successfully returns mentions."""
        test_client, app = client
        app.config["API_KEY"] = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = [
            {
                "text": "<p>Test mention</p>",
                "id": "123",
                "account": "testuser",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/mentions")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "mentions" in data
        assert len(data["mentions"]) == 1
        assert data["mentions"][0]["text"] == "Test mention"  # HTML stripped
        assert "count" in data

    def test_mentions_endpoint_limit_parameter(self, client):
        """Test mentions endpoint with limit parameter."""
        test_client, app = client
        app.config["API_KEY"] = None
        mock_platform = Mock()
        mock_platform.get_latest_mentions.return_value = []
        app.config["PLATFORMS"] = {"mastodon": mock_platform}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/mentions?limit=5")

        assert response.status_code == 200
        mock_platform.get_latest_mentions.assert_called_once_with(limit=5)


class TestPlatformsEndpoint:
    """Tests for /api/v1/platforms endpoint."""

    def test_platforms_endpoint(self, client):
        """Test platforms endpoint."""
        test_client, app = client
        app.config["API_KEY"] = None
        app.config["PLATFORMS"] = {"mastodon": Mock(), "bluesky": Mock()}
        app.config["ACTIVE_PLATFORM"] = "mastodon"

        response = test_client.get("/api/v1/platforms")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "available_platforms" in data
        assert "active_platform" in data
        assert "mastodon" in data["available_platforms"]


class TestConfiguration:
    """Tests for configuration loading."""

    def test_create_app_with_config_override(self):
        """Test creating app with config override."""
        app = create_app(
            config_override={
                "API_KEY": "override-key",
                "SERVER_PORT": 8080,
                "PLATFORMS": {},
                "ACTIVE_PLATFORM": None,
            }
        )
        assert app.config["API_KEY"] == "override-key"
        assert app.config["SERVER_PORT"] == 8080

    def test_create_app_defaults(self):
        """Test creating app has correct defaults when no config."""
        with patch("app.load_config") as mock_load:
            mock_load.return_value = {}
            app = create_app()
            assert app.config["API_KEY"] is None
            assert app.config["SERVER_PORT"] == 5000
            assert app.config["PLATFORMS"] == {}
            assert app.config["ACTIVE_PLATFORM"] is None

    def test_create_app_loads_api_key(self, mock_config):
        """Test that create_app loads API key from config."""
        import configparser

        config = configparser.ConfigParser()
        config.read_dict(mock_config)

        with patch("app.load_config") as mock_load:
            mock_load.return_value = config
            app = create_app()
            assert app.config["API_KEY"] == "test-api-key"

    def test_create_app_loads_server_port(self, mock_config):
        """Test that create_app loads server port from config."""
        import configparser

        config = configparser.ConfigParser()
        config.read_dict(mock_config)

        with patch("app.load_config") as mock_load:
            mock_load.return_value = config
            app = create_app()
            assert app.config["SERVER_PORT"] == 8080
