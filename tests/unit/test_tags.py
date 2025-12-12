"""Unit tests for tagging system."""

import pytest
from src.core.tags import assign_tags, CardTag, STATIC_CARD_TAGS


def test_static_tag_sol_ring():
    """Test static mapping for Sol Ring."""
    tags = assign_tags("Sol Ring", "Artifact", "Tap: Add two colorless mana.")
    
    assert CardTag.RAMP in tags
    assert CardTag.ARTIFACT in tags


def test_static_tag_command_tower():
    """Test static mapping for Command Tower."""
    tags = assign_tags("Command Tower", "Land", "Tap: Add one mana...")
    
    assert CardTag.LAND in tags
    assert CardTag.RAMP in tags


def test_land_detection():
    """Test automatic land detection."""
    tags = assign_tags("Forest", "Basic Land — Forest", "Tap: Add G.")
    
    assert CardTag.LAND in tags


def test_artifact_type_tag():
    """Test automatic artifact type tagging."""
    tags = assign_tags(
        "Unknown Artifact",
        "Artifact",
        "Some ability"
    )
    
    assert CardTag.ARTIFACT in tags


def test_creature_type_tag():
    """Test automatic creature type tagging."""
    tags = assign_tags(
        "Grizzly Bears",
        "Creature — Bear",
        "2/2"
    )
    
    assert CardTag.CREATURE in tags


def test_ramp_detection_from_oracle():
    """Test ramp detection from oracle text."""
    tags = assign_tags(
        "Custom Ramp Card",
        "Sorcery",
        "Add three green mana to your mana pool."
    )
    
    assert CardTag.RAMP in tags
    assert CardTag.SORCERY in tags


def test_draw_detection():
    """Test card draw detection from oracle text."""
    tags = assign_tags(
        "Custom Draw Spell",
        "Instant",
        "Draw a card."
    )
    
    assert CardTag.DRAW in tags
    assert CardTag.INSTANT in tags


def test_removal_detection():
    """Test removal detection from oracle text."""
    tags = assign_tags(
        "Murder",
        "Instant",
        "Destroy target creature."
    )
    
    assert CardTag.REMOVAL in tags


def test_counterspell_detection():
    """Test counterspell detection from oracle text."""
    tags = assign_tags(
        "Custom Counter",
        "Instant",
        "Counter target spell."
    )
    
    assert CardTag.COUNTERSPELL in tags


def test_board_wipe_detection():
    """Test board wipe detection from oracle text."""
    tags = assign_tags(
        "Custom Wrath",
        "Sorcery",
        "Destroy all creatures."
    )
    
    assert CardTag.BOARD_WIPE in tags


def test_tutor_detection():
    """Test tutor detection from oracle text."""
    tags = assign_tags(
        "Custom Tutor",
        "Sorcery",
        "Search your library for a card and put it into your hand."
    )
    
    assert CardTag.TUTOR in tags


def test_multiple_tags():
    """Test card with multiple tags."""
    tags = assign_tags(
        "Treasure Cruise",
        "Instant",
        "Delve. Draw three cards."
    )
    
    # Should have both INSTANT and DRAW
    assert CardTag.INSTANT in tags
    assert CardTag.DRAW in tags


def test_static_mappings_complete():
    """Verify static mappings are defined."""
    # Check a few key cards exist
    assert "Sol Ring" in STATIC_CARD_TAGS
    assert "Arcane Signet" in STATIC_CARD_TAGS
    assert "Command Tower" in STATIC_CARD_TAGS
    assert "Cultivate" in STATIC_CARD_TAGS
    assert "Rhystic Study" in STATIC_CARD_TAGS
    assert "Swords to Plowshares" in STATIC_CARD_TAGS
    assert "Counterspell" in STATIC_CARD_TAGS
    assert "Demonic Tutor" in STATIC_CARD_TAGS
