"""Fixtures for integration tests."""

import os
import subprocess
import time
import configparser

import pytest
import requests


@pytest.fixture
def live_config():
    """Load real credentials from environment variables or config.ini.

    Environment variables take precedence (for CI-friendly configuration).
    Falls back to config.ini for local development.
    """
    config = {}

    # Try environment variables first
    if os.environ.get("MASTODON_INSTANCE_URL"):
        config["mastodon"] = {
            "instance_url": os.environ["MASTODON_INSTANCE_URL"],
            "access_token": os.environ.get("MASTODON_ACCESS_TOKEN", ""),
        }

    if os.environ.get("BLUESKY_IDENTIFIER"):
        config["bluesky"] = {
            "identifier": os.environ["BLUESKY_IDENTIFIER"],
            "password": os.environ.get("BLUESKY_PASSWORD", ""),
        }

    # Fall back to config.ini if no env vars
    if not config:
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.ini")
        if os.path.exists(config_path):
            parser = configparser.ConfigParser()
            parser.read(config_path)

            if "mastodon" in parser:
                config["mastodon"] = dict(parser["mastodon"])
            if "bluesky" in parser:
                config["bluesky"] = dict(parser["bluesky"])

    return config


@pytest.fixture
def docker_container(request):
    """Start jacket-server container for testing.

    Uses docker compose to build and start the container.
    Waits for the container to become healthy before yielding.
    Cleans up the container after the test.
    """
    project_root = os.path.join(os.path.dirname(__file__), "..", "..")

    # Build and start the container
    subprocess.run(
        ["docker", "compose", "build"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )

    subprocess.run(
        ["docker", "compose", "up", "-d"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )

    # Wait for container to be healthy
    base_url = "http://localhost:5000"
    max_retries = 30
    retry_interval = 1

    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/", timeout=2)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(retry_interval)
    else:
        # Cleanup and fail if container didn't start
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=project_root,
            capture_output=True,
        )
        pytest.fail("Container failed to become healthy within timeout")

    yield {"base_url": base_url, "project_root": project_root}

    # Cleanup: stop and remove the container
    subprocess.run(
        ["docker", "compose", "down"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def integration_client():
    """Create a test client with reset state for integration tests."""
    import app

    app.app.config["TESTING"] = True
    app.platforms = {}
    app.active_platform = None
    app.api_key = None
    app.server_port = 5000

    with app.app.test_client() as client:
        yield client
