"""Core data models for MTG Commander Sim."""

from typing import Optional
from pydantic import BaseModel, Field, computed_field, field_validator


class Card(BaseModel):
    """Represents a Magic: The Gathering card with tag-based abstraction."""
    
    name: str
    mana_cost: dict[str, int] = Field(
        default_factory=dict,
        description="Parsed mana cost, e.g., {'R': 1, 'G': 1, 'colorless': 2}"
    )
    cmc: int = Field(ge=0, description="Converted Mana Cost (total)")
    type_line: str = Field(description="e.g., 'Creature — Human Wizard'")
    oracle_text: str = Field(default="", description="Card rules text")
    tags: list[str] = Field(
        default_factory=list,
        description="Functional tags like ['RAMP', 'ARTIFACT']"
    )
    scryfall_id: str = Field(description="Scryfall UUID")
    color_identity: list[str] = Field(
        default_factory=list,
        description="Color identity for Commander format (e.g., ['R', 'G'])"
    )
    
    @computed_field
    @property
    def is_land(self) -> bool:
        """Check if this card is a land based on type line."""
        return "Land" in self.type_line
    
    @property
    def is_permanent(self) -> bool:
        """
        Check if this card is a permanent.
        
        Permanents: Artifact, Creature, Enchantment, Planeswalker, Land
        Non-Permanents: Instant, Sorcery
        """
        # Instants and Sorceries are NOT permanents (go to graveyard after casting)
        if "Instant" in self.type_line or "Sorcery" in self.type_line:
            return False
        
        # Everything else (Artifact, Creature, Enchantment, Planeswalker, Land) is permanent
        return True
    
    def __str__(self) -> str:
        """Pretty string representation."""
        tags_str = ", ".join(self.tags) if self.tags else "No tags"
        return f"{self.name} (CMC: {self.cmc}) [{tags_str}]"
    
    class Config:
        """Pydantic config."""
        frozen = False
        extra = "ignore"


class Deck(BaseModel):
    """Represents a Commander deck (100 cards total: 1 commander + 99 main deck)."""
    
    commander: Card
    cards: list[Card] = Field(description="Main deck (should be 99 cards)")
    
    @field_validator("cards")
    @classmethod
    def validate_deck_size(cls, v: list[Card], info) -> list[Card]:
        """Ensure deck has exactly 99 cards (excluding commander)."""
        if len(v) != 99:
            raise ValueError(f"Deck must have exactly 99 cards, got {len(v)}")
        return v
    
    @computed_field
    @property
    def all_cards(self) -> list[Card]:
        """Get all 100 cards (commander + deck)."""
        return [self.commander] + self.cards
    
    @computed_field
    @property
    def land_count(self) -> int:
        """Count lands in the deck."""
        return sum(1 for card in self.all_cards if card.is_land)
    
    @computed_field
    @property
    def avg_cmc(self) -> float:
        """Calculate average converted mana cost (excluding lands)."""
        non_lands = [card for card in self.all_cards if not card.is_land]
        if not non_lands:
            return 0.0
        return sum(card.cmc for card in non_lands) / len(non_lands)
    
    def get_tag_distribution(self) -> dict[str, int]:
        """Get distribution of tags across all cards."""
        tag_counts: dict[str, int] = {}
        for card in self.all_cards:
            for tag in card.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return tag_counts
    
    def __str__(self) -> str:
        """Pretty string representation."""
        return (
            f"Commander: {self.commander.name}\n"
            f"Deck Size: {len(self.cards)} cards\n"
            f"Lands: {self.land_count}\n"
            f"Avg CMC: {self.avg_cmc:.2f}"
        )
    
    class Config:
        """Pydantic config."""
        frozen = False
