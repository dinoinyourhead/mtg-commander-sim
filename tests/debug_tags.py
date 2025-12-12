
import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.scryfall import fetch_cards
from core.tags import assign_tags

async def main():
    names = ["Coldsteel Heart", "Wayfarer's Bauble", "Fire Diamond", "Star Compass"]
    print(f"🔍 Fetching tags for: {names}")
    
    cards = await fetch_cards(names, use_cache=True)
    
    for card in cards:
        print(f"\n🃏 {card.name}")
        print(f"   Type: {card.type_line}")
        print(f"   Oracle: {card.oracle_text[:50]}...")
        print(f"   Tags: {card.tags}")
        
if __name__ == "__main__":
    asyncio.run(main())
