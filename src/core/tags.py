"""Tagging system for categorizing card functionality."""

import re
from enum import Enum


class CardTag(str, Enum):
    """Tags for categorizing card functionality."""
    # Basic types
    LAND = "LAND"
    ARTIFACT = "ARTIFACT"
    CREATURE = "CREATURE"
    ENCHANTMENT = "ENCHANTMENT"
    INSTANT = "INSTANT"
    SORCERY = "SORCERY"
    PLANESWALKER = "PLANESWALKER"
    
    # Functional categories
    RAMP = "RAMP"
    DRAW = "DRAW"
    REMOVAL = "REMOVAL"
    COUNTERSPELL = "COUNTERSPELL"
    BOARD_WIPE = "BOARD_WIPE"
    TUTOR = "TUTOR"
    
    # Land-specific
    TAPPED_ENTRY = "TAPPED_ENTRY"  # Enters the battlefield tapped
    
    # New specific tags
    MANA_ROCK = "MANA_ROCK"  # Artifact that taps for mana directly


# Static mappings for well-known cards
STATIC_CARD_TAGS: dict[str, list[str]] = {
    # Mana rocks
    "Sol Ring": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Arcane Signet": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Mana Crypt": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Mana Vault": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Chrome Mox": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Mox Diamond": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Fellwar Stone": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Thought Vessel": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Mind Stone": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Talisman of Dominance": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Talisman of Progress": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Talisman of Creativity": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Talisman of Conviction": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Talisman of Hierarchy": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Coldsteel Heart": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK, CardTag.TAPPED_ENTRY],
    "Fire Diamond": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK, CardTag.TAPPED_ENTRY],
    "Marble Diamond": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK, CardTag.TAPPED_ENTRY],
    "Sky Diamond": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK, CardTag.TAPPED_ENTRY],
    "Moss Diamond": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK, CardTag.TAPPED_ENTRY],
    "Charcoal Diamond": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK, CardTag.TAPPED_ENTRY],
    "Star Compass": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK, CardTag.TAPPED_ENTRY],
    "Prismatic Lens": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Thran Dynamo": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Hedron Archive": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    "Gilded Lotus": [CardTag.RAMP, CardTag.ARTIFACT, CardTag.MANA_ROCK],
    
    # Special lands
    "Command Tower": [CardTag.LAND, CardTag.RAMP],
    "Arcane Lighthouse": [CardTag.LAND],
    "Reliquary Tower": [CardTag.LAND],
    "Urborg, Tomb of Yawgmoth": [CardTag.LAND, CardTag.RAMP],
    "Cabal Coffers": [CardTag.LAND, CardTag.RAMP],
    
    # Ramp spells
    "Rampant Growth": [CardTag.RAMP, CardTag.SORCERY],
    "Cultivate": [CardTag.RAMP, CardTag.SORCERY],
    "Kodama's Reach": [CardTag.RAMP, CardTag.SORCERY],
    "Farseek": [CardTag.RAMP, CardTag.SORCERY],
    "Nature's Lore": [CardTag.RAMP, CardTag.SORCERY],
    "Three Visits": [CardTag.RAMP, CardTag.SORCERY],
    "Skyshroud Claim": [CardTag.RAMP, CardTag.SORCERY],
    
    # Ramp creatures
    "Llanowar Elves": [CardTag.RAMP, CardTag.CREATURE],
    "Arbor Elf": [CardTag.RAMP, CardTag.CREATURE],
    "Birds of Paradise": [CardTag.RAMP, CardTag.CREATURE],
    "Fyndhorn Elves": [CardTag.RAMP, CardTag.CREATURE],
    "Sakura-Tribe Elder": [CardTag.RAMP, CardTag.CREATURE],
    
    # Card draw
    "Rhystic Study": [CardTag.DRAW, CardTag.ENCHANTMENT],
    "Mystic Remora": [CardTag.DRAW, CardTag.ENCHANTMENT],
    "Phyrexian Arena": [CardTag.DRAW, CardTag.ENCHANTMENT],
    "Sylvan Library": [CardTag.DRAW, CardTag.ENCHANTMENT],
    
    # Removal
    "Swords to Plowshares": [CardTag.REMOVAL, CardTag.INSTANT],
    "Path to Exile": [CardTag.REMOVAL, CardTag.INSTANT],
    "Assassin's Trophy": [CardTag.REMOVAL, CardTag.INSTANT],
    "Beast Within": [CardTag.REMOVAL, CardTag.INSTANT],
    "Chaos Warp": [CardTag.REMOVAL, CardTag.INSTANT],
    "Generous Gift": [CardTag.REMOVAL, CardTag.INSTANT],
    
    # Board wipes
    "Wrath of God": [CardTag.BOARD_WIPE, CardTag.SORCERY],
    "Damnation": [CardTag.BOARD_WIPE, CardTag.SORCERY],
    "Cyclonic Rift": [CardTag.BOARD_WIPE, CardTag.INSTANT],
    "Blasphemous Act": [CardTag.BOARD_WIPE, CardTag.SORCERY],
    
    # Counterspells
    "Counterspell": [CardTag.COUNTERSPELL, CardTag.INSTANT],
    "Swan Song": [CardTag.COUNTERSPELL, CardTag.INSTANT],
    "Mana Drain": [CardTag.COUNTERSPELL, CardTag.INSTANT],
    "Force of Will": [CardTag.COUNTERSPELL, CardTag.INSTANT],
    "Pact of Negation": [CardTag.COUNTERSPELL, CardTag.INSTANT],
    
    # Tutors
    "Demonic Tutor": [CardTag.TUTOR, CardTag.SORCERY],
    "Vampiric Tutor": [CardTag.TUTOR, CardTag.INSTANT],
    "Worldly Tutor": [CardTag.TUTOR, CardTag.INSTANT],
    "Mystical Tutor": [CardTag.TUTOR, CardTag.INSTANT],
    "Enlightened Tutor": [CardTag.TUTOR, CardTag.INSTANT],
}


def assign_tags(card_name: str, type_line: str, oracle_text: str) -> list[str]:
    """
    Assign functional tags to a card based on name, type, and oracle text.
    
    Args:
        card_name: Card name
        type_line: Card type (e.g., "Creature — Human Wizard")
        oracle_text: Card's rules text
    
    Returns:
        List of tag strings
    """
    tags: set[str] = set()
    
    # 1. Check static mappings first
    if card_name in STATIC_CARD_TAGS:
        tags.update(STATIC_CARD_TAGS[card_name])
    
    # 2. Automatic land detection
    if "Land" in type_line:
        tags.add(CardTag.LAND)
    
    # 3. Add card type tags
    if "Artifact" in type_line:
        tags.add(CardTag.ARTIFACT)
    if "Creature" in type_line:
        tags.add(CardTag.CREATURE)
    if "Enchantment" in type_line:
        tags.add(CardTag.ENCHANTMENT)
    if "Instant" in type_line:
        tags.add(CardTag.INSTANT)
    if "Sorcery" in type_line:
        tags.add(CardTag.SORCERY)
    if "Planeswalker" in type_line:
        tags.add(CardTag.PLANESWALKER)
    
    # 4. Rule-based tagging from oracle text
    oracle_lower = oracle_text.lower()
    
    # Ramp detection
    # Generic Ramp (includes Fetch Ramp)
    if "search your library for a" in oracle_lower and "land" in oracle_lower:
        tags.add(CardTag.RAMP)

    # Mana Rock / Mana Dork detection
    # Pattern: "{T}: Add" or "Add {X}"
    # Valid: "{T}: Add {R}", "Add one mana", "Add three mana"
    # Invalid: "Add a Counter"
    if re.search(r"add\s+.*(\{.*\})|add\s+(one|two|three|any)\s+mana", oracle_lower):
        tags.add(CardTag.MANA_ROCK)
        tags.add(CardTag.RAMP) # All rocks are ramp
    
    # Draw detection
    if re.search(r"draw (a card|cards|\d+ cards?|two cards?|three cards?|four cards?)", oracle_lower):
        tags.add(CardTag.DRAW)
    
    # Removal detection
    if any(word in oracle_lower for word in ["destroy", "exile", "sacrifice"]):
        if any(target in oracle_lower for target in ["creature", "permanent", "target"]):
            tags.add(CardTag.REMOVAL)
    
    # Board wipe detection
    if re.search(r"destroy all (creatures|permanents)", oracle_lower):
        tags.add(CardTag.BOARD_WIPE)
    
    # Counterspell detection
    if "counter target spell" in oracle_lower:
        tags.add(CardTag.COUNTERSPELL)
    
    # Tutor detection
    if re.search(r"search your library for a card", oracle_text, re.IGNORECASE):
        tags.add(CardTag.TUTOR)
    
    # Tapped entry detection (Global - for Lands AND Artifacts)
    # Check for "enters tapped" pattern (various formats)
    # "enters the battlefield tapped" OR "this land enters tapped" OR just "enters tapped" OR "this artifact enters tapped"
    if re.search(r"(this\s+(land|artifact)\s+)?(enters?|enter)\s+(the\s+battlefield\s+)?tapped", oracle_text, re.IGNORECASE):
        tags.add(CardTag.TAPPED_ENTRY)

    # Land-Specific Conditional Logic
    if "Land" in type_line:
        if CardTag.TAPPED_ENTRY in tags:
            # Check for common conditionals that allow it to enter untapped
            # Pattern: "enters tapped unless X" or "enters tapped. X: enter untapped"
            
            # 1. Unless you control 2+ basic lands (most common: dual lands, shock lands)
            if re.search(r"unless you control (two or more|2 or more) basic lands", oracle_lower):
                # Conservatively assume untapped (most decks have basics by turn 2-3)
                tags.remove(CardTag.TAPPED_ENTRY)
            
            # 2. Unless you control Plains/Island/etc (check lands)
            elif re.search(r"unless you control (a|an) (plains|island|swamp|mountain|forest)", oracle_lower):
                # Conservatively assume you have it (remove tapped tag)
                tags.remove(CardTag.TAPPED_ENTRY)
            
            # 3. Unless you reveal/pay life (shock lands, reveal lands)
            # Handle comma: "enters, you may"
            elif re.search(r"(unless you (pay|reveal)|as .*(this\s+)?(land\s+)?enters.* you may (pay|reveal))", oracle_lower):
                # Assume you pay the cost (common in competitive play)
                tags.remove(CardTag.TAPPED_ENTRY)
            
            # 4. Fastlands: Unless you control two or fewer other lands
            # "enters tapped unless you control two or fewer other lands"
            elif re.search(r"unless you control (two|2) or fewer other lands", oracle_lower):
                # Keep TAPPED_ENTRY but add condition tag for engine to check
                tags.add("COND_FASTLAND")

            # 5. Checklands with count: "unless you control 3 or more Mountains" (e.g. Dwarven Mine)
            # Regex to capture the land type (plural)
            elif match := re.search(r"unless you control (three|3) or more other .*(mountains|islands|plains|swamps|forests)", oracle_lower):
                # Valid basic land types
                land_type = match.group(2).upper() # MOUNTAINS, ISLANDS, etc.
                # Remove 'S' from plural to get singular type usually used in type line (MOUNTAIN)
                # But Card.type_line usually has "Mountain", so "MOUNTAIN" is good.
                # Our type check is simple string matching.
                # Tag format: COND_COUNT_3_MOUNTAIN
                tags.add(f"COND_COUNT_3_{land_type[:-1]}") # MOUNTAIN

            # 6. If opponent has more lands than you
            elif re.search(r"unless an opponent (has|controls) more lands", oracle_lower):
                # Conservatively assume it enters tapped (keep tag)
                pass
            
            # 5. Enters tapped if you control X or more lands
            elif re.search(r"enters.*tapped.*if you control (three|3) or more", oracle_lower):
                # Conservatively assume it enters untapped early game
                tags.remove(CardTag.TAPPED_ENTRY)
            
            # Default: If "enters tapped" with no recognized conditional, keep TAPPED_ENTRY tag
    
    return list(tags)
