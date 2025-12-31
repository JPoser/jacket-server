# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Jacket Server is a Python/Flask backend that bridges social media platforms (Mastodon, Bluesky) with an ESP32-controlled RGB LED jacket. It extracts color mentions from social media posts and exposes them via REST API.

## Git Workflow

**Always use feature branches and pull requests** - never push directly to `main`.

1. Create a feature branch: `git checkout -b feature/description`
2. Make changes and commit
3. Push branch: `git push -u origin branch-name`
4. Output PR details (title, summary, test plan) for manual PR creation
5. Wait for review/approval before merging

## Commands

### Development
```bash
python app.py                           # Run locally (debug mode)
gunicorn --bind 0.0.0.0:5000 app:app   # Run with Gunicorn
```

### Testing
```bash
uv run pytest                           # Run all tests with coverage
uv run pytest tests/test_color_parser.py  # Run specific test file
uv run pytest -v                        # Verbose output
```

### Linting & Formatting
```bash
uv run ruff check .                     # Lint
uv run ruff format .                    # Format
uv run pre-commit run --all-files       # Run all pre-commit hooks
```

### Docker
```bash
docker compose up -d --build            # Build and start
docker compose logs -f                  # View logs
```

### Dependencies
```bash
uv sync                                 # Install dependencies
```

## Architecture

### Plugin System
The `platforms/` directory implements a plugin architecture for social media integrations:
- `base.py`: Abstract `SocialPlatform` class defining the interface
- `mastodon.py`: Mastodon API implementation
- `bluesky.py`: Bluesky/AT Protocol implementation

New platforms extend `SocialPlatform` and implement `initialize()` and `get_latest_mentions()`.

### Core Modules
- `app.py`: Flask application with API endpoints, authentication decorator, platform management
- `color_parser.py`: Color and effect detection supporting hex (#RRGGBB), RGB (rgb(r,g,b)), named colors, and LED transition effects

### API Endpoints
- `GET /` - Server status (no auth)
- `GET /api/v1/color` - Extract color from latest mentions
- `GET /api/v1/mentions` - Raw mentions data
- `GET /api/v1/platforms` - Available platforms

All `/api/v1/*` endpoints require `X-API-Key` header when configured.

### Configuration
Copy `config.example.ini` to `config.ini`. Sections: `[server]`, `[mastodon]`, `[bluesky]`.

### Color Detection Priority
1. Hex codes (#RRGGBB)
2. RGB format (rgb(r,g,b))
3. Named colors (20+ supported)
4. Default: white (#ffffff)

### Effect Detection
The API also extracts LED transition effects from mention text. Supported effects:
- **Transition**: fade, wipe_down, wipe_up, wipe_left, wipe_right, chase_down, chase_up, chase_spiral, dissolve, expand
- **Buffer**: colour_stack, colour_rain, colour_trail, colour_waterfall, colour_wave, colour_spiral

Effects can be specified with underscores or spaces (e.g., "wipe down" matches "wipe_down").

## Infrastructure
Terraform configs in `iac/` deploy to Oracle Cloud Infrastructure free tier.
