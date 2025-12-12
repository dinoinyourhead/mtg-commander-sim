"""Unit tests for GameState class."""

import pytest
from src.core.models import Card
from src.core.engine import GameState


def create_test_card(name: str, cmc: int, is_land: bool = False) -> Card:
    """Helper to create a test card."""
    type_line = "Land" if is_land else "Creature"
    return Card(
        name=name,
        mana_cost={"colorless": cmc} if not is_land else {},
        cmc=cmc,
        type_line=type_line,
        oracle_text="",
        tags=["LAND"] if is_land else [],
        scryfall_id=f"test-{name}",
        color_identity=[],
    )


def test_gamestate_init():
    """Test GameState initialization."""
    state = GameState()
    
    assert len(state.library) == 0
    assert len(state.hand) == 0
    assert len(state.battlefield) == 0
    assert len(state.graveyard) == 0
    assert state.turn_counter == 0
    assert state.land_played_this_turn == False
    assert state.mana_pool == {}


def test_draw_card():
    """Test drawing a card from library to hand."""
    state = GameState()
    card1 = create_test_card("Card 1", 1)
    card2 = create_test_card("Card 2", 2)
    
    state.library = [card1, card2]
    
    drawn = state.draw_card()
    
    assert drawn == card1
    assert len(state.library) == 1
    assert len(state.hand) == 1
    assert card1 in state.hand


def test_draw_card_empty_library():
    """Test drawing from empty library returns None."""
    state = GameState()
    
    drawn = state.draw_card()
    
    assert drawn is None
    assert len(state.hand) == 0


def test_play_land():
    """Test playing a land from hand to battlefield."""
    state = GameState()
    land = create_test_card("Forest", 0, is_land=True)
    
    state.hand = [land]
    
    success = state.play_land(land)
    
    assert success == True
    assert len(state.hand) == 0
    assert len(state.battlefield) == 1
    assert land in state.battlefield
    assert state.land_played_this_turn == True


def test_play_land_already_played():
    """Test that only one land can be played per turn."""
    state = GameState()
    land1 = create_test_card("Forest", 0, is_land=True)
    land2 = create_test_card("Mountain", 0, is_land=True)
    
    state.hand = [land1, land2]
    
    # Play first land
    state.play_land(land1)
    
    # Try to play second land
    success = state.play_land(land2)
    
    assert success == False
    assert len(state.battlefield) == 1  # Only first land
    assert land2 in state.hand  # Second land still in hand


def test_play_non_land_as_land():
    """Test that non-lands cannot be played as lands."""
    state = GameState()
    creature = create_test_card("Bear", 2, is_land=False)
    
    state.hand = [creature]
    
    success = state.play_land(creature)
    
    assert success == False
    assert len(state.battlefield) == 0
    assert creature in state.hand


def test_cast_spell():
    """Test casting a spell from hand to battlefield."""
    state = GameState()
    spell = create_test_card("Lightning Bolt", 1)
    
    state.hand = [spell]
    state.mana_pool = {"colorless": 2}
    
    success = state.cast_spell(spell, {"colorless": 1})
    
    assert success == True
    assert len(state.hand) == 0
    assert len(state.battlefield) == 1
    assert spell in state.battlefield
    assert state.mana_pool["colorless"] == 1  # 2 - 1


def test_cast_spell_insufficient_mana():
    """Test that spells cannot be cast without enough mana."""
    state = GameState()
    spell = create_test_card("Expensive Spell", 5)
    
    state.hand = [spell]
    state.mana_pool = {"colorless": 2}
    
    success = state.cast_spell(spell, {"colorless": 5})
    
    assert success == False
    assert spell in state.hand
    assert len(state.battlefield) == 0


def test_add_mana():
    """Test adding mana to the pool."""
    state = GameState()
    
    state.add_mana({"colorless": 3})
    assert state.mana_pool["colorless"] == 3
    
    state.add_mana({"colorless": 2})
    assert state.mana_pool["colorless"] == 5
    
    state.add_mana({"R": 1})
    assert state.mana_pool["R"] == 1


def test_clear_mana_pool():
    """Test clearing the mana pool."""
    state = GameState()
    state.mana_pool = {"colorless": 5, "R": 2}
    
    state.clear_mana_pool()
    
    assert state.mana_pool == {}


def test_can_afford():
    """Test mana affordability check."""
    state = GameState()
    state.mana_pool = {"colorless": 5}
    
    assert state.can_afford({"colorless": 3}) == True
    assert state.can_afford({"colorless": 5}) == True
    assert state.can_afford({"colorless": 6}) == False


def test_get_total_mana():
    """Test total mana calculation."""
    state = GameState()
    
    assert state.get_total_mana() == 0
    
    state.mana_pool = {"colorless": 3, "R": 2}
    assert state.get_total_mana() == 5
