"""Unit tests for Card and Deck models."""

import pytest
from src.core.models import Card, Deck


def test_card_creation():
    """Test basic card creation."""
    card = Card(
        name="Sol Ring",
        mana_cost={"colorless": 1},
        cmc=1,
        type_line="Artifact",
        oracle_text="Tap: Add two colorless mana.",
        tags=["RAMP", "ARTIFACT"],
        scryfall_id="test-id-123",
        color_identity=[],
    )
    
    assert card.name == "Sol Ring"
    assert card.cmc == 1
    assert card.is_land == False
    assert "RAMP" in card.tags


def test_card_is_land():
    """Test land detection."""
    land = Card(
        name="Forest",
        mana_cost={},
        cmc=0,
        type_line="Basic Land — Forest",
        oracle_text="Tap: Add G.",
        tags=["LAND"],
        scryfall_id="test-id-456",
        color_identity=["G"],
    )
    
    assert land.is_land == True


def test_deck_validation():
    """Test deck validation (99 cards + commander)."""
    commander = Card(
        name="Atraxa, Praetors' Voice",
        mana_cost={"W": 1, "U": 1, "B": 1, "G": 1},
        cmc=4,
        type_line="Legendary Creature — Angel Horror",
        oracle_text="Flying, vigilance, deathtouch, lifelink",
        tags=["CREATURE"],
        scryfall_id="commander-id",
        color_identity=["W", "U", "B", "G"],
    )
    
    # Create 99 cards for deck
    cards = []
    for i in range(99):
        cards.append(Card(
            name=f"Card {i}",
            mana_cost={"colorless": 1},
            cmc=1,
            type_line="Artifact",
            oracle_text="",
            tags=[],
            scryfall_id=f"id-{i}",
            color_identity=[],
        ))
    
    deck = Deck(commander=commander, cards=cards)
    
    assert len(deck.all_cards) == 100
    assert deck.commander.name == "Atraxa, Praetors' Voice"


def test_deck_invalid_size():
    """Test that deck validation fails with wrong size."""
    commander = Card(
        name="Commander",
        mana_cost={},
        cmc=0,
        type_line="Legendary Creature",
        oracle_text="",
        tags=[],
        scryfall_id="cmd",
        color_identity=[],
    )
    
    # Only 50 cards (should be 99)
    cards = [
        Card(
            name=f"Card {i}",
            mana_cost={},
            cmc=0,
            type_line="Card",
            oracle_text="",
            tags=[],
            scryfall_id=f"id-{i}",
            color_identity=[],
        )
        for i in range(50)
    ]
    
    with pytest.raises(ValueError, match="must have exactly 99 cards"):
        Deck(commander=commander, cards=cards)


def test_deck_land_count():
    """Test land count calculation."""
    commander = Card(
        name="Commander",
        mana_cost={},
        cmc=0,
        type_line="Legendary Creature",
        oracle_text="",
        tags=[],
        scryfall_id="cmd",
        color_identity=[],
    )
    
    cards = []
    # Add 35 lands
    for i in range(35):
        cards.append(Card(
            name=f"Land {i}",
            mana_cost={},
            cmc=0,
            type_line="Land",
            oracle_text="",
            tags=["LAND"],
            scryfall_id=f"land-{i}",
            color_identity=[],
        ))
    
    # Add 64 non-lands
    for i in range(64):
        cards.append(Card(
            name=f"Spell {i}",
            mana_cost={"colorless": 1},
            cmc=1,
            type_line="Instant",
            oracle_text="",
            tags=[],
            scryfall_id=f"spell-{i}",
            color_identity=[],
        ))
    
    deck = Deck(commander=commander, cards=cards)
    
    assert deck.land_count == 35


def test_deck_avg_cmc():
    """Test average CMC calculation (excluding lands)."""
    commander = Card(
        name="Commander",
        mana_cost={"colorless": 5},
        cmc=5,
        type_line="Legendary Creature",
        oracle_text="",
        tags=[],
        scryfall_id="cmd",
        color_identity=[],
    )
    
    cards = []
    # Add 35 lands (should be excluded from avg)
    for i in range(35):
        cards.append(Card(
            name=f"Land {i}",
            mana_cost={},
            cmc=0,
            type_line="Land",
            oracle_text="",
            tags=["LAND"],
            scryfall_id=f"land-{i}",
            color_identity=[],
        ))
    
    # Add 64 spells with CMC 1-4 (to make exactly 99 cards)
    # 16 cards of each CMC: 1, 2, 3, 4
    for cmc in [1, 2, 3, 4]:
        for i in range(16):
            cards.append(Card(
                name=f"Spell CMC {cmc}-{i}",
                mana_cost={"colorless": cmc},
                cmc=cmc,
                type_line="Sorcery",
                oracle_text="",
                tags=[],
                scryfall_id=f"spell-{cmc}-{i}",
                color_identity=[],
            ))
    
    deck = Deck(commander=commander, cards=cards)
    
    # Average should be: (commander=5 + 16*1 + 16*2 + 16*3 + 16*4) / (1+64) = 165/65 = 2.54
    assert 2.0 <= deck.avg_cmc <= 3.0
