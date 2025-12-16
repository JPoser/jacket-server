"""Jacket Server - Backend for RGB LED jacket controlled via social media mentions."""

from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps
import configparser
import os
from typing import Optional, List, Dict

from platforms.mastodon import MastodonPlatform
from platforms.bluesky import BlueskyPlatform
from color_parser import extract_color, get_default_color


app = Flask(__name__)
CORS(app)  # Enable CORS for ESP32 client

# Global platform instances
platforms: Dict[str, any] = {}
active_platform: Optional[str] = None
api_key: Optional[str] = None
server_port: int = 5000


def load_config():
    """Load configuration from config.ini file."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    if not os.path.exists(config_path):
        print(f"Warning: config.ini not found at {config_path}")
        return config
    
    config.read(config_path)
    return config


def load_api_key():
    """Load API key from configuration."""
    global api_key
    config = load_config()
    
    if 'server' in config:
        api_key = config['server'].get('api_key')
        if api_key:
            print("✓ API key loaded (authentication enabled)")
        else:
            print("⚠ No API key configured (authentication disabled)")
    else:
        print("⚠ No API key configured (authentication disabled)")


def load_server_config():
    """Load server configuration (port, etc.) from config file."""
    global server_port
    config = load_config()
    
    if 'server' in config:
        port_str = config['server'].get('port')
        if port_str:
            try:
                server_port = int(port_str)
                print(f"✓ Server port configured: {server_port}")
            except ValueError:
                print(f"⚠ Invalid port '{port_str}', using default: 5000")
                server_port = 5000
        else:
            print(f"⚠ No port configured, using default: 5000")
    else:
        print(f"⚠ No server config found, using default port: 5000")


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If no API key is configured, allow access (backward compatibility)
        if not api_key:
            return f(*args, **kwargs)
        
        # Check for API key in header only (query parameters can be exposed in logs/DNS)
        provided_key = request.headers.get('X-API-Key')
        
        if not provided_key or provided_key != api_key:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Valid API key required. Provide via X-API-Key header.'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function


def initialize_platforms():
    """Initialize available social media platforms from configuration."""
    global platforms, active_platform
    
    config = load_config()
    
    # Initialize Mastodon if configured
    if 'mastodon' in config:
        mastodon = MastodonPlatform()
        mastodon_config = {
            'instance_url': config['mastodon'].get('instance_url'),
            'access_token': config['mastodon'].get('access_token')
        }
        if mastodon.initialize(mastodon_config):
            platforms['mastodon'] = mastodon
            if not active_platform:
                active_platform = 'mastodon'
            print("✓ Mastodon platform initialized")
        else:
            print("✗ Failed to initialize Mastodon")
    
    # Initialize Bluesky if configured
    if 'bluesky' in config:
        bluesky = BlueskyPlatform()
        bluesky_config = {
            'identifier': config['bluesky'].get('identifier'),
            'password': config['bluesky'].get('password'),
            'debug': config['bluesky'].get('debug', 'false')
        }
        if bluesky.initialize(bluesky_config):
            platforms['bluesky'] = bluesky
            if not active_platform:
                active_platform = 'bluesky'
            print("✓ Bluesky platform initialized")
        else:
            print("✗ Failed to initialize Bluesky")
    
    if not platforms:
        print("Warning: No platforms initialized. Please check your config.ini")


@app.route('/', methods=['GET'])
def index():
    """Root endpoint."""
    return jsonify({
        'message': 'Welcome to Jacket Server',
        'version': '2.0',
        'available_platforms': list(platforms.keys()),
        'active_platform': active_platform
    })


@app.route('/api/v1/color', methods=['GET'])
@require_api_key
def get_color():
    """
    Get the latest color from social media mentions.
    
    Query parameters:
        platform: Optional platform name (mastodon, bluesky). Defaults to active platform.
        limit: Number of mentions to check (default: 10)
    """
    global active_platform
    
    # Get platform from query parameter or use active platform
    platform_name = request.args.get('platform', active_platform)
    limit = int(request.args.get('limit', 10))
    
    if not platform_name or platform_name not in platforms:
        return jsonify({
            'error': f'Platform "{platform_name}" not available',
            'available_platforms': list(platforms.keys())
        }), 400
    
    platform = platforms[platform_name]
    
    try:
        mentions = platform.get_latest_mentions(limit=limit)
        
        if not mentions:
            return jsonify({
                'color': get_default_color(),
                'message': 'No mentions found',
                'platform': platform_name
            })
        
        # Check each mention for color information
        for mention in mentions:
            text = mention.get('text', '')
            # Remove HTML tags if present (Mastodon returns HTML)
            import re
            text = re.sub(r'<[^>]+>', '', text)
            
            color = extract_color(text)
            if color:
                return jsonify({
                    'color': color,
                    'mention': {
                        'text': text,
                        'id': mention.get('id'),
                        'account': mention.get('account', ''),
                        'created_at': mention.get('created_at')
                    },
                    'platform': platform_name
                })
        
        # No color found in any mention
        return jsonify({
            'color': get_default_color(),
            'message': 'No color found in recent mentions',
            'platform': platform_name,
            'mentions_checked': len(mentions)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'platform': platform_name
        }), 500


@app.route('/api/v1/mentions', methods=['GET'])
@require_api_key
def get_mentions():
    """
    Get recent mentions without color extraction.
    
    Query parameters:
        platform: Optional platform name (mastodon, bluesky). Defaults to active platform.
        limit: Number of mentions to fetch (default: 10)
    """
    global active_platform
    
    platform_name = request.args.get('platform', active_platform)
    limit = int(request.args.get('limit', 10))
    
    if not platform_name or platform_name not in platforms:
        return jsonify({
            'error': f'Platform "{platform_name}" not available',
            'available_platforms': list(platforms.keys())
        }), 400
    
    platform = platforms[platform_name]
    
    try:
        mentions = platform.get_latest_mentions(limit=limit)
        
        # Clean HTML from Mastodon mentions
        import re
        cleaned_mentions = []
        for mention in mentions:
            text = mention.get('text', '')
            text = re.sub(r'<[^>]+>', '', text)
            cleaned_mentions.append({
                'text': text,
                'id': mention.get('id'),
                'account': mention.get('account', ''),
                'created_at': mention.get('created_at')
            })
        
        return jsonify({
            'mentions': cleaned_mentions,
            'count': len(cleaned_mentions),
            'platform': platform_name
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'platform': platform_name
        }), 500


@app.route('/api/v1/platforms', methods=['GET'])
@require_api_key
def list_platforms():
    """List available and active platforms."""
    return jsonify({
        'available_platforms': list(platforms.keys()),
        'active_platform': active_platform
    })


if __name__ == '__main__':
    print("Initializing Jacket Server...")
    load_api_key()
    load_server_config()
    initialize_platforms()
    print(f"Server starting with {len(platforms)} platform(s) available")
    app.run(debug=True, host='0.0.0.0', port=server_port)
