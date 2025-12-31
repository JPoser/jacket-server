"""Tests for color parsing functionality."""

from color_parser import (
    parse_hex_color,
    parse_rgb_color,
    find_color_name,
    extract_color,
    extract_effect,
    get_default_color,
    EFFECTS,
)


class TestParseHexColor:
    """Tests for parse_hex_color function."""

    def test_valid_uppercase_hex(self):
        """Test parsing uppercase hex color."""
        result = parse_hex_color("#FF0000")
        assert result == (255, 0, 0)

    def test_valid_lowercase_hex(self):
        """Test parsing lowercase hex color."""
        result = parse_hex_color("#00ff00")
        assert result == (0, 255, 0)

    def test_valid_mixed_case_hex(self):
        """Test parsing mixed case hex color."""
        result = parse_hex_color("#aAbBcC")
        assert result == (170, 187, 204)

    def test_hex_in_text(self):
        """Test extracting hex color from text."""
        result = parse_hex_color("The color is #0000FF today")
        assert result == (0, 0, 255)

    def test_invalid_hex_short(self):
        """Test that short hex codes are not matched."""
        result = parse_hex_color("#FFF")
        assert result is None

    def test_invalid_hex_no_hash(self):
        """Test that hex without hash is not matched."""
        result = parse_hex_color("FF0000")
        assert result is None

    def test_no_hex_in_text(self):
        """Test text without hex color."""
        result = parse_hex_color("This is just text")
        assert result is None

    def test_empty_string(self):
        """Test empty string."""
        result = parse_hex_color("")
        assert result is None


class TestParseRgbColor:
    """Tests for parse_rgb_color function."""

    def test_valid_rgb_no_spaces(self):
        """Test parsing RGB without spaces."""
        result = parse_rgb_color("rgb(255,0,0)")
        assert result == (255, 0, 0)

    def test_valid_rgb_with_spaces(self):
        """Test parsing RGB with spaces."""
        result = parse_rgb_color("rgb(255, 0, 0)")
        assert result == (255, 0, 0)

    def test_valid_rgb_mixed_spaces(self):
        """Test parsing RGB with mixed spacing."""
        result = parse_rgb_color("rgb( 128 , 64 , 32 )")
        assert result == (128, 64, 32)

    def test_rgb_in_text(self):
        """Test extracting RGB from text."""
        result = parse_rgb_color("Use rgb(0,255,0) for green")
        assert result == (0, 255, 0)

    def test_rgb_case_insensitive(self):
        """Test that RGB is case insensitive."""
        result = parse_rgb_color("RGB(100,200,50)")
        assert result == (100, 200, 50)

    def test_invalid_rgb_missing_comma(self):
        """Test invalid RGB format."""
        result = parse_rgb_color("rgb(255 0 0)")
        assert result is None

    def test_invalid_rgb_no_parens(self):
        """Test RGB without parentheses."""
        result = parse_rgb_color("255,0,0")
        assert result is None

    def test_no_rgb_in_text(self):
        """Test text without RGB."""
        result = parse_rgb_color("This is just text")
        assert result is None


class TestFindColorName:
    """Tests for find_color_name function."""

    def test_find_red(self):
        """Test finding red color."""
        result = find_color_name("Make it red!")
        assert result is not None
        assert result[0] == "red"
        assert result[1] == (255, 0, 0)

    def test_find_blue(self):
        """Test finding blue color."""
        result = find_color_name("I like blue colors")
        assert result is not None
        assert result[0] == "blue"
        assert result[1] == (0, 0, 255)

    def test_find_case_insensitive(self):
        """Test that color names are case insensitive."""
        result = find_color_name("RED RED RED")
        assert result is not None
        assert result[0] == "red"

    def test_find_longer_color_name_first(self):
        """Test that longer color names are matched first."""
        # "spring" should match before "green" if both are present
        result = find_color_name("spring green")
        assert result is not None
        assert result[0] == "spring"  # Longer name should match first

    def test_no_color_in_text(self):
        """Test text without color name."""
        result = find_color_name("This is just text")
        assert result is None

    def test_partial_match_found(self):
        """Test that substring matches work (e.g., 'red' in 'reddish')."""
        result = find_color_name("reddish")
        # Should match "red" as it's a substring match (intentional behavior)
        assert result is not None
        assert result[0] == "red"


class TestExtractColor:
    """Tests for extract_color function."""

    def test_extract_hex_priority(self):
        """Test that hex colors have priority."""
        result = extract_color("red #FF0000 blue")
        assert result is not None
        assert result["hex"] == "#ff0000"
        assert result["rgb"] == (255, 0, 0)

    def test_extract_rgb_priority_over_name(self):
        """Test that RGB has priority over color names."""
        result = extract_color("red rgb(0,255,0) blue")
        assert result is not None
        assert result["name"] == "rgb(0, 255, 0)"
        assert result["rgb"] == (0, 255, 0)

    def test_extract_color_name(self):
        """Test extracting color name."""
        result = extract_color("Make it green please")
        assert result is not None
        assert result["name"] == "green"
        assert result["rgb"] == (0, 128, 0)
        assert result["hex"] == "#008000"

    def test_extract_hex_format(self):
        """Test hex color extraction format."""
        result = extract_color("#AABBCC")
        assert result is not None
        assert result["hex"] == "#aabbcc"
        assert result["rgb"] == (170, 187, 204)

    def test_extract_rgb_format(self):
        """Test RGB color extraction format."""
        result = extract_color("rgb(100, 200, 50)")
        assert result is not None
        assert result["name"] == "rgb(100, 200, 50)"
        assert result["rgb"] == (100, 200, 50)
        assert result["hex"] == "#64c832"

    def test_no_color_found(self):
        """Test text with no color."""
        result = extract_color("This is just text")
        assert result is None

    def test_empty_string(self):
        """Test empty string."""
        result = extract_color("")
        assert result is None

    def test_none_input(self):
        """Test None input."""
        result = extract_color(None)
        assert result is None


class TestGetDefaultColor:
    """Tests for get_default_color function."""

    def test_default_color_is_white(self):
        """Test that default color is white."""
        result = get_default_color()
        assert result["name"] == "white"
        assert result["rgb"] == (255, 255, 255)
        assert result["hex"] == "#ffffff"

    def test_default_color_structure(self):
        """Test that default color has correct structure."""
        result = get_default_color()
        assert "name" in result
        assert "rgb" in result
        assert "hex" in result
        assert isinstance(result["rgb"], tuple)
        assert len(result["rgb"]) == 3


class TestExtractEffect:
    """Tests for extract_effect function."""

    def test_extract_fade(self):
        """Test extracting fade effect."""
        result = extract_effect("fade to red")
        assert result == "fade"

    def test_extract_wipe_down(self):
        """Test extracting wipe_down effect."""
        result = extract_effect("wipe_down to blue")
        assert result == "wipe_down"

    def test_extract_wipe_down_with_space(self):
        """Test extracting wipe down with space instead of underscore."""
        result = extract_effect("wipe down to blue")
        assert result == "wipe_down"

    def test_extract_case_insensitive(self):
        """Test that effect extraction is case insensitive."""
        result = extract_effect("FADE to red")
        assert result == "fade"

    def test_extract_colour_spiral(self):
        """Test extracting colour_spiral effect."""
        result = extract_effect("use colour_spiral effect")
        assert result == "colour_spiral"

    def test_extract_colour_spiral_with_space(self):
        """Test extracting colour spiral with space."""
        result = extract_effect("use colour spiral effect")
        assert result == "colour_spiral"

    def test_no_effect_found(self):
        """Test text with no effect."""
        result = extract_effect("make it red")
        assert result is None

    def test_empty_string(self):
        """Test empty string."""
        result = extract_effect("")
        assert result is None

    def test_none_input(self):
        """Test None input."""
        result = extract_effect(None)
        assert result is None

    def test_all_transition_effects_recognized(self):
        """Test that all transition effects are recognized."""
        transition_effects = [
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
        ]
        for effect in transition_effects:
            result = extract_effect(f"use {effect} effect")
            assert result == effect, f"Failed to extract effect: {effect}"

    def test_all_buffer_effects_recognized(self):
        """Test that all buffer effects are recognized."""
        buffer_effects = [
            "colour_stack",
            "colour_rain",
            "colour_trail",
            "colour_waterfall",
            "colour_wave",
            "colour_spiral",
        ]
        for effect in buffer_effects:
            result = extract_effect(f"use {effect} effect")
            assert result == effect, f"Failed to extract effect: {effect}"

    def test_longer_effect_matched_first(self):
        """Test that longer effect names are matched first."""
        # "chase_spiral" should match before "chase_down" if both could match
        result = extract_effect("chase_spiral")
        assert result == "chase_spiral"

    def test_effect_with_color(self):
        """Test extracting effect when color is also present."""
        result = extract_effect("fade to red")
        assert result == "fade"

    def test_effects_set_has_expected_count(self):
        """Test that EFFECTS set has expected number of effects."""
        assert len(EFFECTS) == 16  # 10 transition + 6 buffer effects
