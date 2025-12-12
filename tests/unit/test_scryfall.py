"""Unit tests for Scryfall client with rate limiting and format parsing."""

import pytest
from src.core.scryfall import (
    parse_card_name,
    parse_mana_cost,
)


def test_parse_card_name_plain():
    """Test parsing plain card names."""
    assert parse_card_name("Sol Ring") == "Sol Ring"
    assert parse_card_name("Command Tower") == "Command Tower"


def test_parse_card_name_with_quantity():
    """Test parsing card names with quantities (Archidekt format)."""
    assert parse_card_name("1 Sol Ring") == "Sol Ring"
    assert parse_card_name("3 Forest") == "Forest"
    assert parse_card_name("10 Mountain") == "Mountain"


def test_parse_card_name_with_x_suffix():
    """Test parsing card names with 'x' suffix."""
    assert parse_card_name("1x Sol Ring") == "Sol Ring"
    assert parse_card_name("3x Forest") == "Forest"


def test_parse_card_name_with_set_code():
    """Test parsing card names with set codes in parentheses."""
    assert parse_card_name("Sol Ring (CMD)") == "Sol Ring"
    assert parse_card_name("1 Forest (M21)") == "Forest"
    assert parse_card_name("1x Command Tower (C20)") == "Command Tower"


def test_parse_card_name_empty():
    """Test parsing empty lines."""
    assert parse_card_name("") is None
    assert parse_card_name("   ") is None
    assert parse_card_name("\n") is None


def test_parse_card_name_whitespace():
    """Test parsing with extra whitespace."""
    assert parse_card_name("  1 Sol Ring  ") == "Sol Ring"
    assert parse_card_name("  Forest  ") == "Forest"


def test_parse_mana_cost_simple():
    """Test parsing simple mana costs."""
    result = parse_mana_cost("{2}{R}{G}")
    assert result == {"colorless": 2, "R": 1, "G": 1}


def test_parse_mana_cost_hybrid():
    """Test parsing hybrid mana costs."""
    result = parse_mana_cost("{R/G}{R/G}")
    assert "R" in result
    assert result["R"] == 2


def test_parse_mana_cost_phyrexian():
    """Test parsing Phyrexian mana costs."""
    result = parse_mana_cost("{R/P}{R/P}")
    assert "R" in result
    assert result["R"] == 2


def test_parse_mana_cost_x_spell():
    """Test parsing X spells."""
    result = parse_mana_cost("{X}{U}{U}")
    assert result["X"] == 1
    assert result["U"] == 2


def test_parse_mana_cost_empty():
    """Test parsing empty mana cost."""
    result = parse_mana_cost("")
    assert result == {}


def test_parse_mana_cost_complex():
    """Test parsing complex mana cost."""
    result = parse_mana_cost("{3}{W}{U}{B}")
    assert result == {"colorless": 3, "W": 1, "U": 1, "B": 1}
