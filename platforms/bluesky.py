"""Bluesky platform integration."""

from typing import List, Optional
from atproto import Client, models
from .base import SocialPlatform


class BlueskyPlatform(SocialPlatform):
    """Bluesky platform implementation."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.debug: bool = False
        
    def initialize(self, config: dict) -> bool:
        """Initialize Bluesky client with configuration."""
        try:
            identifier = config.get('identifier')  # username or email
            password = config.get('password')  # app password
            
            # Get debug flag (default: False)
            debug_str = config.get('debug', 'false').lower()
            self.debug = debug_str in ('true', '1', 'yes', 'on')
            
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
            # Request more notifications since we'll filter to only mentions
            # This helps ensure we get enough mentions even if there are many likes/replies
            request_limit = max(limit * 3, 50)  # Request 3x the limit or at least 50
            
            params = models.AppBskyNotificationListNotifications.Params(limit=request_limit)
            notifications = self.client.app.bsky.notification.list_notifications(params=params)
            mentions = []
            
            # Count notification types (always done, but only printed if debug)
            reason_counts = {}
            for notif in notifications.notifications:
                reason = getattr(notif, 'reason', 'NO_REASON')
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            if self.debug:
                print(f"\n=== Bluesky Notifications Debug ===")
                print(f"Total notifications: {len(notifications.notifications)}")
                print(f"Notification types: {reason_counts}")
                mention_count = reason_counts.get('mention', 0)
                reply_count = reason_counts.get('reply', 0)
                print(f"Mentions found: {mention_count}, Replies found: {reply_count}")
                print("=====================================\n")
            
            # Process mentions and replies (replies can also mention you)
            for notification in notifications.notifications:
                reason = getattr(notification, 'reason', None)
                
                # Process both mentions and replies (replies might mention you)
                if reason not in ['mention', 'reply']:
                    continue
                
                if self.debug:
                    print(f"Found {reason} notification: {getattr(notification, 'uri', 'no uri')}")
                
                # Try to get post URI from different possible locations
                post_uri = None
                
                # Method 1: Check if notification has subject with URI
                if hasattr(notification, 'subject') and notification.subject:
                    post_uri = getattr(notification.subject, 'uri', None)
                    if post_uri and self.debug:
                        print(f"  Got URI from subject: {post_uri}")
                
                # Method 2: For replies, the notification URI itself might be the post URI
                # Check if it's a post URI (app.bsky.feed.post)
                if not post_uri and hasattr(notification, 'uri'):
                    uri = notification.uri
                    if 'app.bsky.feed.post' in uri:
                        post_uri = uri
                        if self.debug:
                            print(f"  Got post URI from notification.uri: {post_uri}")
                    elif self.debug:
                        print(f"  Notification URI is not a post: {uri}")
                
                if not post_uri:
                    if self.debug:
                        print(f"  WARNING: No post URI found for {reason} notification")
                    continue
                
                try:
                    # Try to get post data from notification first (might be embedded)
                    text = ''
                    author_handle = ''
                    
                    # Check if notification has embedded post data
                    if hasattr(notification, 'record') and notification.record:
                        record = notification.record
                        text = getattr(record, 'text', '')
                        if self.debug:
                            print(f"  Found text in notification.record: {text[:50]}...")
                    
                    # If not in notification, fetch it
                    if not text:
                        if self.debug:
                            print(f"  Fetching post from URI: {post_uri}")
                        # Use get_posts (plural) with uris parameter
                        posts_data = self.client.app.bsky.feed.get_posts(uris=[post_uri])
                        
                        if posts_data and posts_data.posts and len(posts_data.posts) > 0:
                            post = posts_data.posts[0]
                            if hasattr(post, 'record') and post.record:
                                record = post.record
                                text = getattr(record, 'text', '')
                                if self.debug:
                                    print(f"  Successfully fetched post with text: {text[:50]}...")
                                
                                # Get author handle
                                if hasattr(post, 'author') and post.author:
                                    author_handle = getattr(post.author, 'handle', '')
                        else:
                            if self.debug:
                                print(f"  ERROR: No post data returned from get_posts")
                            continue
                    else:
                        # Get author handle from notification
                        if hasattr(notification, 'author') and notification.author:
                            author_handle = getattr(notification.author, 'handle', '')
                    
                    if not text:
                        if self.debug:
                            print(f"  ERROR: Could not extract text from post")
                        continue
                    
                    # Get author handle if not already set
                    if not author_handle:
                        if hasattr(notification, 'author') and notification.author:
                            author_handle = getattr(notification.author, 'handle', '')
                    
                    mentions.append({
                        'text': text,
                        'id': post_uri,
                        'created_at': getattr(notification, 'indexed_at', None),
                        'account': author_handle
                    })
                    
                    if self.debug:
                        print(f"  Added mention to list (total: {len(mentions)})")
                    
                    # Stop once we have enough mentions
                    if len(mentions) >= limit:
                        break
                        
                except Exception as fetch_error:
                    if self.debug:
                        print(f"  ERROR fetching post: {fetch_error}")
                        import traceback
                        traceback.print_exc()
                    continue
            
            return mentions
        except Exception as e:
            # Always print errors, even if debug is off
            print(f"Error fetching Bluesky mentions: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return []

