# Jacket Server

Backend server for controlling an RGB LED jacket via social media mentions. Supports Mastodon and Bluesky platforms.

## Features

- **Multi-platform support**: Mastodon and Bluesky integrations
- **Advanced color detection**: Supports color names, hex codes (#RRGGBB), and RGB values
- **RESTful API**: Clean endpoints for ESP32 clients
- **Extensible architecture**: Easy to add new social media platforms

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Platforms

Copy the example config file and fill in your credentials:

```bash
cp config.example.ini config.ini
```

Edit `config.ini` with your platform credentials:

#### Server Configuration

1. Set a pre-shared API key in the `[server]` section
2. Use a strong, random key (e.g., generate with `openssl rand -hex 32`)
3. If no key is set, authentication is disabled (not recommended for production)
4. Configure the server port (default: 5000) in the `[server]` section

#### Mastodon Setup

1. Go to your Mastodon instance settings
2. Navigate to **Development** → **New Application**
3. Create an application with `read:notifications` scope
4. Copy the access token to `config.ini`

#### Bluesky Setup

1. Go to https://bsky.app/settings/app-passwords
2. Create a new app password
3. Use your username/email and the app password in `config.ini`

**Note**: You only need to configure the platforms you want to use. The server will automatically use the first successfully initialized platform.

### 3. Run the Server

```bash
python app.py
```

The server will start on `http://0.0.0.0:<port>` where `<port>` is the value configured in `config.ini` (default: 5000).

## API Endpoints

### `GET /`

Root endpoint showing server status and available platforms.

**Response:**
```json
{
  "message": "Welcome to Jacket Server",
  "version": "2.0",
  "available_platforms": ["mastodon", "bluesky"],
  "active_platform": "mastodon"
}
```

### `GET /api/v1/color`

Get the latest color from social media mentions.

**Authentication:** Required (if API key is configured)

**Headers:**
- `X-API-Key`: Your pre-shared API key (required)

**Query Parameters:**
- `platform` (optional): Platform name (`mastodon` or `bluesky`). Defaults to active platform.
- `limit` (optional): Number of mentions to check (default: 10)

**Response:**
```json
{
  "color": {
    "name": "red",
    "rgb": [255, 0, 0],
    "hex": "#ff0000"
  },
  "mention": {
    "text": "Make it red!",
    "id": "12345",
    "account": "username",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "platform": "mastodon"
}
```

### `GET /api/v1/mentions`

Get recent mentions without color extraction.

**Authentication:** Required (if API key is configured)

**Headers:**
- `X-API-Key`: Your pre-shared API key (required)

**Query Parameters:**
- `platform` (optional): Platform name
- `limit` (optional): Number of mentions to fetch (default: 10)

### `GET /api/v1/platforms`

List available and active platforms.

**Authentication:** Required (if API key is configured)

**Headers:**
- `X-API-Key`: Your pre-shared API key (required)

## Color Detection

The server detects colors in multiple formats:

1. **Color Names**: `red`, `blue`, `green`, `cyan`, `magenta`, etc.
2. **Hex Codes**: `#FF0000`, `#00ff00`, `#0000FF`
3. **RGB Format**: `rgb(255,0,0)`, `rgb(0, 255, 0)`

If no color is found, the server returns white (`#ffffff`) as the default.

## ESP32 Integration

Your ESP32 client can poll the `/api/v1/color` endpoint to get the latest color:

```cpp
// Example Arduino/ESP32 code
HTTPClient http;
http.begin("https://your-server:5000/api/v1/color");  // Use HTTPS for security
http.addHeader("X-API-Key", "your-api-key-here");  // Add authentication header
int httpCode = http.GET();

if (httpCode == 200) {
  String payload = http.getString();
  // Parse JSON and extract RGB values
  // Apply to your LED strip
} else if (httpCode == 401) {
  // Authentication failed - check your API key
}
```

**Note:** Always use HTTPS in production to ensure the API key header is encrypted in transit.

## Testing with curl

Here are some curl command examples to test the API endpoints:

### Root Endpoint (No Authentication Required)

```bash
# Check server status
curl http://localhost:5000/
```

### Color Endpoint

```bash
# Get latest color (with authentication)
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api/v1/color

# Get color from specific platform
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api/v1/color?platform=mastodon

# Get color with custom mention limit
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api/v1/color?limit=5
```

### Mentions Endpoint

```bash
# Get recent mentions
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api/v1/mentions

# Get mentions from specific platform
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api/v1/mentions?platform=bluesky

# Get mentions with custom limit
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api/v1/mentions?limit=20
```

### Platforms Endpoint

```bash
# List available platforms
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api/v1/platforms
```

### Testing Authentication

```bash
# Test without API key (should return 401 if authentication is enabled)
curl http://localhost:5000/api/v1/color

# Test with invalid API key (should return 401)
curl -H "X-API-Key: wrong-key" http://localhost:5000/api/v1/color
```

### Pretty Print JSON Responses

For better readability, pipe the output through `jq` (if installed):

```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api/v1/color | jq
```

Or use Python's json.tool:

```bash
curl -H "X-API-Key: your-api-key-here" http://localhost:5000/api/v1/color | python -m json.tool
```

## Architecture

The codebase uses a plugin-based architecture:

- `platforms/base.py`: Abstract base class for platform integrations
- `platforms/mastodon.py`: Mastodon implementation
- `platforms/bluesky.py`: Bluesky implementation
- `color_parser.py`: Color detection and parsing utilities
- `app.py`: Main Flask application

To add a new platform, create a new class in `platforms/` that inherits from `SocialPlatform` and implement the required methods.

## License

See LICENSE file.

