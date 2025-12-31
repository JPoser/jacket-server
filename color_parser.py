"""Color parsing and detection utilities."""

import re
from typing import Optional, Tuple


# Extended color name mappings with RGB values
COLOR_MAP = {
    "red": (255, 0, 0),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "chartreuse": (127, 255, 0),
    "green": (0, 128, 0),
    "spring": (0, 255, 127),
    "cyan": (0, 255, 255),
    "azure": (0, 127, 255),
    "blue": (0, 0, 255),
    "violet": (138, 43, 226),
    "magenta": (255, 0, 255),
    "rose": (255, 20, 147),
    "pink": (255, 192, 203),
    "purple": (128, 0, 128),
    "indigo": (75, 0, 130),
    "turquoise": (64, 224, 208),
    "lime": (0, 255, 0),
    "amber": (255, 191, 0),
    "coral": (255, 127, 80),
    "salmon": (250, 128, 114),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
}

# Supported effect names for LED transitions
EFFECTS = {
    # Transition effects
    "fade",
    "wipe_down",
    "wipe_up",
    "wipe_left",
    "wipe_right",
    "chase_down",
    "chase_up",
    "chase_spiral",
    "dissolve",
    "expand",
    # Buffer effects
    "colour_stack",
    "colour_rain",
    "colour_trail",
    "colour_waterfall",
    "colour_wave",
    "colour_spiral",
}


def parse_hex_color(text: str) -> Optional[Tuple[int, int, int]]:
    """Extract hex color code from text (e.g., #FF0000, #ff00ff)."""
    hex_pattern = r"#([0-9A-Fa-f]{6})"
    match = re.search(hex_pattern, text)
    if match:
        hex_code = match.group(1)
        return (int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16))
    return None


def parse_rgb_color(text: str) -> Optional[Tuple[int, int, int]]:
    """Extract RGB color from text (e.g., rgb(255,0,0), rgb(255, 0, 0))."""
    rgb_pattern = r"rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)"
    match = re.search(rgb_pattern, text, re.IGNORECASE)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return None


def find_color_name(text: str) -> Optional[Tuple[str, Tuple[int, int, int]]]:
    """Find color name in text and return name with RGB tuple."""
    text_lower = text.lower()

    # Check for exact color names (longer names first to avoid partial matches)
    sorted_colors = sorted(COLOR_MAP.items(), key=lambda x: len(x[0]), reverse=True)

    for color_name, rgb in sorted_colors:
        if color_name in text_lower:
            return (color_name, rgb)

    return None


def extract_color(text: str) -> Optional[dict]:
    """
    Extract color information from text.

    Priority:
    1. Hex color codes (#RRGGBB)
    2. RGB format (rgb(r,g,b))
    3. Color names

    Returns:
        Dictionary with 'name', 'rgb', and 'hex' keys, or None if no color found
    """
    if not text:
        return None

    # Try hex color first
    rgb = parse_hex_color(text)
    if rgb:
        return {
            "name": f"#{''.join(f'{c:02x}' for c in rgb)}",
            "rgb": rgb,
            "hex": f"#{''.join(f'{c:02x}' for c in rgb)}",
        }

    # Try RGB format
    rgb = parse_rgb_color(text)
    if rgb:
        return {
            "name": f"rgb{rgb}",
            "rgb": rgb,
            "hex": f"#{''.join(f'{c:02x}' for c in rgb)}",
        }

    # Try color names
    color_result = find_color_name(text)
    if color_result:
        color_name, rgb = color_result
        return {
            "name": color_name,
            "rgb": rgb,
            "hex": f"#{''.join(f'{c:02x}' for c in rgb)}",
        }

    return None


def get_default_color() -> dict:
    """Return default white color."""
    return {"name": "white", "rgb": (255, 255, 255), "hex": "#ffffff"}


def extract_effect(text: str) -> Optional[str]:
    """
    Extract effect name from text.

    Searches for effect keywords (case-insensitive). Underscores can be
    replaced with spaces (e.g., "wipe down" matches "wipe_down").

    Returns:
        Effect name if found, or None if no effect found
    """
    if not text:
        return None

    text_lower = text.lower()

    # Check for effects (longer names first to avoid partial matches)
    sorted_effects = sorted(EFFECTS, key=len, reverse=True)

    for effect in sorted_effects:
        # Match with underscores or spaces
        if effect in text_lower or effect.replace("_", " ") in text_lower:
            return effect

    return None
