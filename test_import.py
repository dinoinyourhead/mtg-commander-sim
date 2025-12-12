"""
Phase 1 Validation Script: Test card import from Scryfall.

This script demonstrates the core functionality of Phase 1:
1. Reading a decklist from a text file
2. Fetching card data from Scryfall API
3. Parsing mana costs and assigning tags
4. Displaying card information
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.scryfall import fetch_cards


def print_header():
    """Print a nice header."""
    print("=" * 60)
    print("MTG Commander Sim - Card Import Test (Phase 1)")
    print("=" * 60)
    print()


def print_card_details(cards: list):
    """Print detailed information about fetched cards."""
    print(f"\n✓ Successfully loaded {len(cards)} cards\n")
    print("-" * 60)
    
    for i, card in enumerate(cards, 1):
        print(f"\n{i}. {card.name}")
        print(f"   CMC: {card.cmc}")
        print(f"   Type: {card.type_line}")
        
        # Format mana cost
        if card.mana_cost:
            mana_str = ", ".join(f"{k}: {v}" for k, v in card.mana_cost.items())
            print(f"   Mana Cost: {{{mana_str}}}")
        else:
            print(f"   Mana Cost: None")
        
        # Format tags
        if card.tags:
            tags_str = ", ".join(card.tags)
            print(f"   Tags: [{tags_str}]")
        else:
            print(f"   Tags: [No tags]")
        
        # Show if it's a land
        if card.is_land:
            print(f"   🟢 Land card")
    
    print("\n" + "-" * 60)


async def main():
    """Main entry point."""
    print_header()
    
    # Path to sample decklist
    decklist_path = Path(__file__).parent / "data" / "sample_decklist.txt"
    
    if not decklist_path.exists():
        print(f"❌ Error: Sample decklist not found at {decklist_path}")
        return
    
    print(f"📂 Loading cards from: {decklist_path}")
    
    # Read decklist lines
    with open(decklist_path, "r") as f:
        lines = f.readlines()
    
    print("\nFetching cards from Scryfall API...")
    print("(This may take a few seconds due to rate limiting)\n")
    
    # Fetch full deck with duplicates
    from core.scryfall import fetch_deck_from_decklist
    cards = await fetch_deck_from_decklist(lines)
    
    # Display results
    if cards:
        print(f"\n✓ Successfully built deck with {len(cards)} cards")
        print("-" * 60)
        
        # Group by unique cards for display
        from collections import Counter
        card_counts = Counter(card.name for card in cards)
        
        print(f"\n📋 Unique Cards ({len(card_counts)}):\n")
        
        for i, (card_name, count) in enumerate(sorted(card_counts.items()), 1):
            # Get the card object for details
            card = next(c for c in cards if c.name == card_name)
            
            count_str = f"{count}x" if count > 1 else "1 "
            print(f"{i:2d}. {count_str} {card.name}")
            print(f"     CMC: {card.cmc} | Type: {card.type_line}")
            
            # Format mana cost
            if card.mana_cost:
                mana_str = ", ".join(f"{k}: {v}" for k, v in card.mana_cost.items())
                print(f"     Mana: {{{mana_str}}}")
            
            # Format tags
            if card.tags:
                tags_str = ", ".join(card.tags)
                print(f"     Tags: [{tags_str}]")
            
            if card.is_land:
                print(f"     🟢 Land card")
            
            print()
        
        print("-" * 60)
        
        # Summary statistics for FULL DECK (with duplicates)
        print("\n📊 Deck Statistics (100 Cards):")
        print(f"   Total cards: {len(cards)}")
        print(f"   Unique cards: {len(card_counts)}")
        print(f"   Lands: {sum(1 for c in cards if c.is_land)}")
        
        non_lands = [c for c in cards if not c.is_land]
        if non_lands:
            avg_cmc = sum(c.cmc for c in non_lands) / len(non_lands)
            print(f"   Average CMC (non-lands): {avg_cmc:.2f}")
        
        # Tag distribution (counting duplicates)
        tag_counts = {}
        for card in cards:
            for tag in card.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        if tag_counts:
            print(f"\n   Tag Distribution (with duplicates):")
            for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
                print(f"     - {tag}: {count}")
        
        print("\n✅ Phase 1 validation complete!")
        print(f"🎯 Deck ready for simulation with {len(cards)} cards!")
    else:
        print("❌ No cards were fetched successfully.")


if __name__ == "__main__":
    asyncio.run(main())
