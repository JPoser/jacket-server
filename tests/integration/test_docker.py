"""Integration tests for the Docker container.

These tests build and run the actual Docker container,
then verify it responds correctly.

To run these tests:
    uv run pytest tests/integration/test_docker.py -v -m docker

Requirements:
    - Docker daemon running
    - config.ini present (can be minimal for basic tests)
"""

import pytest
import requests


@pytest.mark.docker
class TestDockerContainer:
    """Test the built Docker container."""

    def test_container_starts_and_becomes_healthy(self, docker_container):
        """Container starts and becomes healthy within timeout."""
        # If we got here, the fixture already verified the container is healthy
        assert docker_container is not None
        assert "base_url" in docker_container

    def test_root_endpoint_responds(self, docker_container):
        """Root endpoint returns expected response."""
        base_url = docker_container["base_url"]

        response = requests.get(f"{base_url}/", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "available_platforms" in data

    def test_platforms_endpoint_responds(self, docker_container):
        """Platforms endpoint returns valid response."""
        base_url = docker_container["base_url"]

        response = requests.get(f"{base_url}/api/v1/platforms", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert "available_platforms" in data
        assert isinstance(data["available_platforms"], list)

    def test_color_endpoint_responds(self, docker_container):
        """Color endpoint responds (may error without platforms, that's okay)."""
        base_url = docker_container["base_url"]

        response = requests.get(f"{base_url}/api/v1/color", timeout=5)

        # Should get either 200 (success) or 400 (no platforms) or 401 (auth required)
        assert response.status_code in [200, 400, 401]

    def test_mentions_endpoint_responds(self, docker_container):
        """Mentions endpoint responds (may error without platforms, that's okay)."""
        base_url = docker_container["base_url"]

        response = requests.get(f"{base_url}/api/v1/mentions", timeout=5)

        # Should get either 200 (success) or 400 (no platforms) or 401 (auth required)
        assert response.status_code in [200, 400, 401]

    def test_invalid_endpoint_returns_404(self, docker_container):
        """Invalid endpoint returns 404."""
        base_url = docker_container["base_url"]

        response = requests.get(f"{base_url}/api/v1/nonexistent", timeout=5)

        assert response.status_code == 404

    def test_container_handles_concurrent_requests(self, docker_container):
        """Container handles multiple concurrent requests."""
        import concurrent.futures

        base_url = docker_container["base_url"]

        def make_request():
            return requests.get(f"{base_url}/", timeout=5)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)


@pytest.mark.docker
class TestDockerHealthCheck:
    """Test Docker health check functionality."""

    def test_health_check_endpoint_works(self, docker_container):
        """The health check endpoint used by Docker works."""
        base_url = docker_container["base_url"]

        # The health check calls the root endpoint
        response = requests.get(f"{base_url}/", timeout=5)

        assert response.status_code == 200


@pytest.mark.docker
class TestDockerEnvironment:
    """Test Docker container environment configuration."""

    def test_container_respects_port_config(self, docker_container):
        """Container runs on configured port."""
        base_url = docker_container["base_url"]

        # Default port is 5000
        assert "5000" in base_url

        response = requests.get(f"{base_url}/", timeout=5)
        assert response.status_code == 200

    def test_gunicorn_workers_running(self, docker_container):
        """Gunicorn is running with workers (container serves requests)."""
        base_url = docker_container["base_url"]

        # If Gunicorn is running properly, we can make requests
        response = requests.get(f"{base_url}/", timeout=5)

        assert response.status_code == 200
        # Verify it's actually returning JSON (Gunicorn serving Flask)
        assert response.headers.get("Content-Type", "").startswith("application/json")
