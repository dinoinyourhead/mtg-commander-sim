"""Integration tests for Scryfall API client."""

import pytest
from src.core.scryfall import (
    fetch_cards,
    parse_mana_cost,
    create_card_from_scryfall_data,
)


def test_parse_mana_cost_simple():
    """Test parsing simple mana costs."""
    result = parse_mana_cost("{2}{R}{G}")
    
    assert result == {"colorless": 2, "R": 1, "G": 1}


def test_parse_mana_cost_hybrid():
    """Test parsing hybrid mana costs."""
    result = parse_mana_cost("{R/G}{R/G}")
    
    # Hybrid counts as first color
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


@pytest.mark.asyncio
async def test_fetch_cards_integration():
    """
    Integration test for fetching real cards from Scryfall.
    
    This test makes real API calls. It may be slow due to rate limiting.
    """
    card_names = ["Sol Ring", "Command Tower", "Forest"]
    
    cards = await fetch_cards(card_names)
    
    # Should fetch all 3 cards
    assert len(cards) == 3
    
    # Check Sol Ring
    sol_ring = next(c for c in cards if c.name == "Sol Ring")
    assert sol_ring.cmc == 1
    assert "RAMP" in sol_ring.tags
    assert "ARTIFACT" in sol_ring.tags
    
    # Check Command Tower
    command_tower = next(c for c in cards if c.name == "Command Tower")
    assert command_tower.is_land
    assert "LAND" in command_tower.tags
    
    # Check Forest
    forest = next(c for c in cards if c.name == "Forest")
    assert forest.is_land
    assert forest.cmc == 0


@pytest.mark.asyncio
async def test_fetch_cards_missing():
    """Test handling of missing cards."""
    card_names = ["Sol Ring", "This Card Does Not Exist 123456789"]
    
    cards = await fetch_cards(card_names)
    
    # Should only fetch Sol Ring
    assert len(cards) == 1
    assert cards[0].name == "Sol Ring"


def test_create_card_from_scryfall_data():
    """Test creating a Card object from Scryfall data."""
    # Sample Scryfall response
    scryfall_data = {
        "name": "Sol Ring",
        "mana_cost": "{1}",
        "cmc": 1,
        "type_line": "Artifact",
        "oracle_text": "{T}: Add {C}{C}.",
        "id": "123-456-789",
        "color_identity": [],
    }
    
    card = create_card_from_scryfall_data(scryfall_data)
    
    assert card.name == "Sol Ring"
    assert card.cmc == 1
    assert card.mana_cost == {"colorless": 1}
    assert "RAMP" in card.tags
    assert "ARTIFACT" in card.tags
