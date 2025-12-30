#!/bin/bash
# Run live integration tests against real Mastodon and Bluesky APIs
#
# Requirements:
#   - Valid credentials in config.ini or environment variables
#
# Environment variables (optional, override config.ini):
#   MASTODON_INSTANCE_URL - e.g., https://fosstodon.org
#   MASTODON_ACCESS_TOKEN - API access token
#   BLUESKY_IDENTIFIER - username or email
#   BLUESKY_PASSWORD - app password
#
# Usage:
#   ./scripts/test-live.sh           # Run all live tests
#   ./scripts/test-live.sh mastodon  # Run only Mastodon tests
#   ./scripts/test-live.sh bluesky   # Run only Bluesky tests

set -e

cd "$(dirname "$0")/.."

echo "Running live integration tests..."
echo "================================="
echo ""

if [ -n "$1" ]; then
    # Run specific platform tests
    case "$1" in
        mastodon)
            echo "Running Mastodon live tests only..."
            uv run pytest tests/integration/test_live_platforms.py -v -m live -k "Mastodon"
            ;;
        bluesky)
            echo "Running Bluesky live tests only..."
            uv run pytest tests/integration/test_live_platforms.py -v -m live -k "Bluesky"
            ;;
        *)
            echo "Unknown platform: $1"
            echo "Usage: $0 [mastodon|bluesky]"
            exit 1
            ;;
    esac
else
    # Run all live tests
    uv run pytest tests/integration/test_live_platforms.py -v -m live
fi

echo ""
echo "Live tests completed!"
