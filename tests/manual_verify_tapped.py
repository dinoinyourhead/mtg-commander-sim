import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.scryfall import fetch_cards

async def test():
    test_lands = [
        ('Path of Ancestry', True),      # Always tapped
        ('Temple of Malady', True),      # Always tapped  
        ('Sunpetal Grove', False),       # Unless control Forest/Plains (Conditional -> Untapped)
        ('Temple Garden', False),        # Pay 2 life (Conditional -> Untapped)
        ('Command Tower', False),        # Never tapped
        ('Myriad Landscape', True),      # Always tapped
        ('Spire of Industry', False),    # No "enters tapped" text
    ]
    
    print('🔄 Fetching cards...')
    # Use cache to be fast
    cards = await fetch_cards([name for name, _ in test_lands], use_cache=True)
    
    print('\n🏞️  Land Tapped Detection Test:\n')
    all_correct = True
    
    # Create map for easier lookup
    card_map = {c.name: c for c in cards}
    
    for name, expected_tapped in test_lands:
        if name not in card_map:
            print(f'❌ Card not found: {name}')
            all_correct = False
            continue
            
        card = card_map[name]
        actual_tapped = 'TAPPED_ENTRY' in card.tags
        
        status = '✅' if expected_tapped == actual_tapped else '❌'
        if expected_tapped != actual_tapped:
            all_correct = False
        
        tapped_str = '🔴 TAPPED' if actual_tapped else '🟢 UNTAPPED'
        print(f'{status} {tapped_str:15} {card.name}')
        
        if expected_tapped != actual_tapped:
            print(f"   [DEBUG] Oracle: {card.oracle_text!r}")
            # print(f"   [DEBUG] Tags: {card.tags}")
    
    print(f'\n{"✅ All correct!" if all_correct else "❌ Some errors found"}')

if __name__ == "__main__":
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\nTest interrupted")
