"""Shared pytest fixtures for all tests."""


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "live: marks tests that hit real external APIs")
    config.addinivalue_line("markers", "docker: marks tests that require Docker")
