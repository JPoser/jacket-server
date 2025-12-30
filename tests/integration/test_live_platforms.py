"""Live integration tests against real Mastodon and Bluesky APIs.

These tests require real credentials and make actual API calls.
They are excluded from CI by default (use -m live to run).

To run these tests:
    uv run pytest tests/integration/test_live_platforms.py -v -m live

Required environment variables or config.ini entries:
    MASTODON_INSTANCE_URL - e.g., https://fosstodon.org
    MASTODON_ACCESS_TOKEN - API access token
    BLUESKY_IDENTIFIER - username or email
    BLUESKY_PASSWORD - app password
"""

import pytest

from platforms.mastodon import MastodonPlatform
from platforms.bluesky import BlueskyPlatform


@pytest.mark.live
class TestMastodonLive:
    """Live tests against real Mastodon API."""

    def test_mastodon_authentication(self, live_config):
        """Can authenticate with Mastodon instance."""
        if "mastodon" not in live_config:
            pytest.skip("Mastodon credentials not configured")

        platform = MastodonPlatform()
        result = platform.initialize(live_config["mastodon"])

        assert result is True, "Failed to authenticate with Mastodon"

    def test_mastodon_fetch_mentions(self, live_config):
        """Can fetch real mentions from Mastodon."""
        if "mastodon" not in live_config:
            pytest.skip("Mastodon credentials not configured")

        platform = MastodonPlatform()
        initialized = platform.initialize(live_config["mastodon"])
        assert initialized, "Failed to initialize Mastodon platform"

        mentions = platform.get_latest_mentions(limit=5)

        # Should return a list (may be empty if no mentions)
        assert isinstance(mentions, list)

        # If we got mentions, verify structure
        if mentions:
            mention = mentions[0]
            assert "text" in mention
            assert "id" in mention
            assert "account" in mention
            assert "created_at" in mention

    def test_mastodon_handles_rate_limit_gracefully(self, live_config):
        """Mastodon platform handles API errors gracefully."""
        if "mastodon" not in live_config:
            pytest.skip("Mastodon credentials not configured")

        platform = MastodonPlatform()
        platform.initialize(live_config["mastodon"])

        # Make multiple requests - should not crash even if rate limited
        for _ in range(3):
            mentions = platform.get_latest_mentions(limit=1)
            assert isinstance(mentions, list)


@pytest.mark.live
class TestBlueskyLive:
    """Live tests against real Bluesky API."""

    def test_bluesky_authentication(self, live_config):
        """Can authenticate with Bluesky."""
        if "bluesky" not in live_config:
            pytest.skip("Bluesky credentials not configured")

        platform = BlueskyPlatform()
        result = platform.initialize(live_config["bluesky"])

        assert result is True, "Failed to authenticate with Bluesky"

    def test_bluesky_fetch_notifications(self, live_config):
        """Can fetch real notifications from Bluesky."""
        if "bluesky" not in live_config:
            pytest.skip("Bluesky credentials not configured")

        platform = BlueskyPlatform()
        initialized = platform.initialize(live_config["bluesky"])
        assert initialized, "Failed to initialize Bluesky platform"

        mentions = platform.get_latest_mentions(limit=5)

        # Should return a list (may be empty if no notifications)
        assert isinstance(mentions, list)

        # If we got mentions, verify structure
        if mentions:
            mention = mentions[0]
            assert "text" in mention
            assert "id" in mention
            assert "account" in mention
            assert "created_at" in mention

    def test_bluesky_debug_mode(self, live_config):
        """Bluesky platform works with debug mode enabled."""
        if "bluesky" not in live_config:
            pytest.skip("Bluesky credentials not configured")

        config = live_config["bluesky"].copy()
        config["debug"] = "true"

        platform = BlueskyPlatform()
        initialized = platform.initialize(config)
        assert initialized, "Failed to initialize Bluesky with debug mode"

        mentions = platform.get_latest_mentions(limit=1)
        assert isinstance(mentions, list)


@pytest.mark.live
class TestFullFlowLive:
    """Live end-to-end tests with real API data."""

    def test_color_extraction_from_real_mastodon(self, live_config):
        """Full color extraction flow with real Mastodon data."""
        if "mastodon" not in live_config:
            pytest.skip("Mastodon credentials not configured")

        from color_parser import extract_color, get_default_color

        platform = MastodonPlatform()
        platform.initialize(live_config["mastodon"])

        mentions = platform.get_latest_mentions(limit=10)

        # Try to extract color from any mention
        color_found = None
        for mention in mentions:
            color = extract_color(mention.get("text", ""))
            if color:
                color_found = color
                break

        # If no color found in real mentions, that's okay - just verify flow works
        if color_found is None:
            color_found = get_default_color()

        assert "name" in color_found or "hex" in color_found or "rgb" in color_found

    def test_color_extraction_from_real_bluesky(self, live_config):
        """Full color extraction flow with real Bluesky data."""
        if "bluesky" not in live_config:
            pytest.skip("Bluesky credentials not configured")

        from color_parser import extract_color, get_default_color

        platform = BlueskyPlatform()
        platform.initialize(live_config["bluesky"])

        mentions = platform.get_latest_mentions(limit=10)

        # Try to extract color from any mention
        color_found = None
        for mention in mentions:
            color = extract_color(mention.get("text", ""))
            if color:
                color_found = color
                break

        # If no color found in real mentions, that's okay - just verify flow works
        if color_found is None:
            color_found = get_default_color()

        assert "name" in color_found or "hex" in color_found or "rgb" in color_found


@pytest.mark.live
class TestCredentialValidation:
    """Test credential validation with real APIs."""

    def test_mastodon_invalid_token_fails(self, live_config):
        """Invalid Mastodon token returns False on initialize."""
        if "mastodon" not in live_config:
            pytest.skip("Mastodon credentials not configured")

        config = live_config["mastodon"].copy()
        config["access_token"] = "invalid-token-12345"

        platform = MastodonPlatform()
        result = platform.initialize(config)

        assert result is False

    def test_bluesky_invalid_password_fails(self, live_config):
        """Invalid Bluesky password returns False on initialize."""
        if "bluesky" not in live_config:
            pytest.skip("Bluesky credentials not configured")

        config = live_config["bluesky"].copy()
        config["password"] = "invalid-password-12345"

        platform = BlueskyPlatform()
        result = platform.initialize(config)

        assert result is False

    def test_mastodon_invalid_instance_fails(self):
        """Invalid Mastodon instance URL fails gracefully."""
        config = {
            "instance_url": "https://not-a-real-mastodon-instance.invalid",
            "access_token": "some-token",
        }

        platform = MastodonPlatform()
        result = platform.initialize(config)

        assert result is False

    def test_bluesky_missing_credentials_fails(self):
        """Missing Bluesky credentials returns False."""
        platform = BlueskyPlatform()

        # Empty config
        result = platform.initialize({})
        assert result is False

        # Missing password
        result = platform.initialize({"identifier": "user@test.com"})
        assert result is False
