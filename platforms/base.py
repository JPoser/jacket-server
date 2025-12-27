"""Base class for social media platform integrations."""

from abc import ABC, abstractmethod
from typing import List


class SocialPlatform(ABC):
    """Abstract base class for social media platform integrations."""

    @abstractmethod
    def get_latest_mentions(self, limit: int = 10) -> List[dict]:
        """
        Fetch the latest mentions/notifications from the platform.

        Args:
            limit: Maximum number of mentions to fetch

        Returns:
            List of mention dictionaries with 'text' and 'id' keys
        """
        pass

    @abstractmethod
    def initialize(self, config: dict) -> bool:
        """
        Initialize the platform connection with configuration.

        Args:
            config: Platform-specific configuration dictionary

        Returns:
            True if initialization successful, False otherwise
        """
        pass
