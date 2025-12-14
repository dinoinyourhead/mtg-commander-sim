"""
10-Turn Goldfish Simulation Test

Loads a deck, runs 10 turns, and outputs statistics.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.scryfall import fetch_deck_from_decklist
from core.engine import GameEngine


def print_header():
    """Print test header."""
    print("=" * 70)
    print("MTG Commander Sim - Engine Test (10 Turns)")
    print("=" * 70)
    print()


async def main():
    """Main test function."""
    import argparse
    from datetime import datetime
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="MTG Commander Sim - 10-Turn Goldfish Simulation"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (turn-by-turn details)"
    )
    parser.add_argument(
        "--log", "-l",
        action="store_true",
        help="Save game log to logs/ directory with timestamp"
    )
    parser.add_argument(
        "--turns", "-t",
        type=int,
        default=10,
        help="Number of turns to simulate (default: 10)"
    )
    parser.add_argument(
        "--commander", "-c",
        type=str,
        default=None,
        help="Commander name (overrides decklist)"
    )
    parser.add_argument(
        "--deck", "-d",
        type=str,
        default="data/sample_decklist.txt",
        help="Path to decklist file"
    )
    
    args = parser.parse_args()
    
    print_header()
    
    # Load deck
    decklist_path = Path(__file__).parent.parent / args.deck
    
    if not decklist_path.exists():
        print(f"❌ Error: Decklist not found at {decklist_path}")
        return
    
    print(f"📂 Loading deck from: {decklist_path.name}")
    
    with open(decklist_path, "r") as f:
        lines = f.readlines()
    
    print("🔄 Fetching cards from Scryfall...")
    deck, commander_name = await fetch_deck_from_decklist(lines, args.commander)
    
    if len(deck) < 50:
        print(f"⚠️  Warning: Deck only has {len(deck)} cards (expected ~100)")
    
    print(f"✓ Deck loaded: {len(deck)} cards\n")
    
    # Get commander card object if specified
    commander_card = None
    if commander_name:
        # Try to find commander in deck
        for card in deck:
            if card.name == commander_name:
                commander_card = card
                break
    
    # Initialize engine with verbose flag from args
    engine = GameEngine(verbose=args.verbose)
    
    # Start game
    print("🎮 Starting game...")
    engine.start_game(deck, commander_card)
    
    commander_name = engine.state.commander.name if engine.state.commander else "None"
    print(f"   Commander: {commander_name}")
    print(f"   Library: {len(engine.state.library)} cards")
    print(f"   Opening hand: {len(engine.state.hand)} cards")
    print()
    
    # Run N turns (from args)
    print(f"🎲 Running {args.turns}-turn simulation...\n")
    
    if not args.verbose:
        # Only show table if not verbose
        print(f"{'Turn':<6} {'Mana':<8} {'Battlefield':<12} {'Hand':<8} {'Library':<8}")
        print("-" * 70)
    
    for turn in range(1, args.turns + 1):
        # Execute turn
        engine.step()
        
        # Get stats
        summary = engine.get_summary()
        
        # Print stats (only if not verbose)
        if not args.verbose:
            print(
                f"{summary['turn']:<6} "
                f"{summary['lands_on_battlefield']:<8} "
                f"{summary['battlefield_size']:<12} "
                f"{summary['hand_size']:<8} "
                f"{summary['library_size']:<8}"
            )
    
    if not args.verbose:
        print("-" * 70)
    
    # Final summary
    final = engine.get_summary()
    print("\n📊 Final Statistics:")
    print(f"   Turns played: {final['turn'] - 1}")
    print(f"   Lands on battlefield: {final['lands_on_battlefield']}")
    print(f"   Total permanents: {final['battlefield_size']}")
    print(f"   Cards in hand: {final['hand_size']}")
    print(f"   Cards in library: {final['library_size']}")
    
    # Analyze deck performance
    print("\n📈 Deck Performance Analysis:")
    
    # Land ratio
    lands_in_deck = len([c for c in deck if c.is_land])
    land_ratio = lands_in_deck / len(deck) * 100
    print(f"   Land ratio in deck: {land_ratio:.1f}% ({lands_in_deck}/{len(deck)})")
    
    # Mana curve check
    if final['lands_on_battlefield'] < 4:
        print("   ⚠️  Warning: Low land count on turn 10 - possible mana screw")
    elif final['lands_on_battlefield'] >= 4:
        print(f"   ✓ Good land drops: {final['lands_on_battlefield']} lands by turn {args.turns}")
    
    # Spell velocity
    spells_played = final['battlefield_size'] - final['lands_on_battlefield']
    print(f"   Spells cast: {spells_played} non-land permanents")
    
    if spells_played < 5:
        print("   ⚠️  Warning: Low spell count - deck may be slow")
    else:
        print(f"   ✓ Good spell velocity: {spells_played} spells in {args.turns} turns")
    
    # Export log if requested
    if args.log:
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"sim_{timestamp}.json"
        log_path = log_dir / log_filename
        
        engine.export_log(str(log_path))
        print(f"\n💾 Game log saved to: {log_path.relative_to(Path(__file__).parent.parent)}")
        print(f"   ({len(engine.game_log)} events logged)")
    
    print("\n✅ Simulation complete!")


if __name__ == "__main__":
    asyncio.run(main())
