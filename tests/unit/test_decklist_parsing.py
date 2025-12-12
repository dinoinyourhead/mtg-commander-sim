"""Tests for decklist parsing and deck expansion."""

import pytest
from src.core.scryfall import parse_decklist


def test_parse_decklist_plain():
    """Test parsing plain card names."""
    lines = ["Sol Ring", "Command Tower", "Forest"]
    result = parse_decklist(lines)
    
    assert len(result) == 3
    assert result[0] == ("Sol Ring", 1)
    assert result[1] == ("Command Tower", 1)
    assert result[2] == ("Forest", 1)


def test_parse_decklist_with_quantities():
    """Test parsing with quantities (Archidekt format)."""
    lines = ["1 Sol Ring", "10 Forest", "3 Island"]
    result = parse_decklist(lines)
    
    assert len(result) == 3
    assert result[0] == ("Sol Ring", 1)
    assert result[1] == ("Forest", 10)
    assert result[2] == ("Island", 3)


def test_parse_decklist_with_x_suffix():
    """Test parsing with 'x' suffix."""
    lines = ["1x Sol Ring", "3x Forest"]
    result = parse_decklist(lines)
    
    assert len(result) == 2
    assert result[0] == ("Sol Ring", 1)
    assert result[1] == ("Forest", 3)


def test_parse_decklist_with_comments():
    """Test that comments are ignored."""
    lines = [
        "# Commander",
        "1 Atraxa, Praetors' Voice",
        "# Lands",
        "10 Forest"
    ]
    result = parse_decklist(lines)
    
    assert len(result) == 2
    assert result[0] == ("Atraxa, Praetors' Voice", 1)
    assert result[1] == ("Forest", 10)


def test_parse_decklist_with_set_codes():
    """Test that set codes are removed."""
    lines = ["1 Sol Ring (CMD)", "10 Forest (M21)"]
    result = parse_decklist(lines)
    
    assert len(result) == 2
    assert result[0] == ("Sol Ring", 1)
    assert result[1] == ("Forest", 10)


def test_parse_decklist_empty_lines():
    """Test that empty lines are ignored."""
    lines = ["1 Sol Ring", "", "  ", "10 Forest"]
    result = parse_decklist(lines)
    
    assert len(result) == 2


def test_parse_decklist_total_count():
    """Test calculating total card count."""
    lines = ["1 Sol Ring", "10 Forest", "3 Island", "1 Command Tower"]
    result = parse_decklist(lines)
    
    total = sum(qty for _, qty in result)
    assert total == 15


@pytest.mark.asyncio
async def test_fetch_deck_from_decklist_integration():
    """Integration test: fetch and expand to full deck."""
    from src.core.scryfall import fetch_deck_from_decklist
    
    lines = [
        "1 Sol Ring",
        "3 Forest",
        "1 Command Tower"
    ]
    
    deck = await fetch_deck_from_decklist(lines)
    
    # Should have 5 total cards (1 + 3 + 1)
    assert len(deck) == 5
    
    # Check duplicates
    forest_count = sum(1 for card in deck if card.name == "Forest")
    assert forest_count == 3
    
    sol_ring_count = sum(1 for card in deck if card.name == "Sol Ring")
    assert sol_ring_count == 1
