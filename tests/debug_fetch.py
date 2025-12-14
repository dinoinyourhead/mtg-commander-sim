
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.scryfall import fetch_cards

async def main():
    print("🔍 Debugging Terramorphic Expanse Tags...")
    cards = await fetch_cards(["Terramorphic Expanse", "Evolving Wilds"])
    
    for card in cards:
        print(f"\nName: {card.name}")
        print(f"Oracle: {card.oracle_text}")
        print(f"Tags: {card.tags}")
        
        if "TAPPED_ENTRY" in card.tags:
            print("✅ Has TAPPED_ENTRY")
        else:
            print("❌ MISSING TAPPED_ENTRY")
            
        if "FETCH_LAND" in card.tags:
            print("✅ Has FETCH_LAND")
        else:
            print("❌ MISSING FETCH_LAND")

if __name__ == "__main__":
    asyncio.run(main())
