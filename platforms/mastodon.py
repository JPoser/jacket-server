"""Mastodon platform integration."""

from typing import List, Optional
from mastodon import Mastodon
from .base import SocialPlatform


class MastodonPlatform(SocialPlatform):
    """Mastodon platform implementation."""
    
    def __init__(self):
        self.client: Optional[Mastodon] = None
        self.instance_url: Optional[str] = None
        
    def initialize(self, config: dict) -> bool:
        """Initialize Mastodon client with configuration."""
        try:
            self.instance_url = config.get('instance_url')
            access_token = config.get('access_token')
            
            if not self.instance_url or not access_token:
                return False
                
            self.client = Mastodon(
                access_token=access_token,
                api_base_url=self.instance_url
            )
            # Verify connection by fetching account info
            self.client.account_verify_credentials()
            return True
        except Exception as e:
            print(f"Error initializing Mastodon: {e}")
            return False
    
    def get_latest_mentions(self, limit: int = 10) -> List[dict]:
        """Fetch latest mentions from Mastodon."""
        if not self.client:
            return []
            
        try:
            # Get notifications (mentions)
            notifications = self.client.notifications(limit=limit)
            mentions = []
            
            for notification in notifications:
                if notification['type'] == 'mention':
                    status = notification.get('status', {})
                    mentions.append({
                        'text': status.get('content', ''),
                        'id': status.get('id'),
                        'created_at': status.get('created_at'),
                        'account': status.get('account', {}).get('username', '')
                    })
            
            return mentions
        except Exception as e:
            print(f"Error fetching Mastodon mentions: {e}")
            return []

