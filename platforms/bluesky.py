"""Bluesky platform integration."""

from typing import List, Optional
from atproto import Client, models
from .base import SocialPlatform


class BlueskyPlatform(SocialPlatform):
    """Bluesky platform implementation."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        
    def initialize(self, config: dict) -> bool:
        """Initialize Bluesky client with configuration."""
        try:
            identifier = config.get('identifier')  # username or email
            password = config.get('password')  # app password
            
            if not identifier or not password:
                return False
                
            self.client = Client()
            self.client.login(login=identifier, password=password)
            return True
        except Exception as e:
            print(f"Error initializing Bluesky: {e}")
            return False
    
    def get_latest_mentions(self, limit: int = 10) -> List[dict]:
        """Fetch latest mentions from Bluesky."""
        if not self.client:
            return []
            
        try:
            # Get notifications (mentions)
            notifications = self.client.app.bsky.notification.list_notifications(limit=limit)
            mentions = []
            
            for notification in notifications.notifications:
                if notification.reason == 'mention':
                    # Fetch the post details
                    post_uri = notification.uri
                    post_ref = models.AppBskyFeedGetPost.Params(uri=post_uri)
                    post_data = self.client.app.bsky.feed.get_post(params=post_ref)
                    
                    if post_data.post:
                        record = post_data.post.record
                        mentions.append({
                            'text': getattr(record, 'text', ''),
                            'id': notification.uri,
                            'created_at': notification.indexed_at,
                            'account': notification.author.handle
                        })
            
            return mentions
        except Exception as e:
            print(f"Error fetching Bluesky mentions: {e}")
            return []

