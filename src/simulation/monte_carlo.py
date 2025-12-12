
import argparse
import asyncio
import os
import sys
import time
from collections import defaultdict
import statistics

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from core.engine import GameEngine
from core.scryfall import fetch_deck_from_decklist

async def run_simulation(deck_lines: list[str], commander_name: str, num_sims: int, turns: int):
    """Run Monte Carlo simulation."""
    print(f"🚀 Starting Monte Carlo Simulation: {num_sims} games, {turns} turns each")
    print("   Fetching deck...")
    
    # Fetch deck ONCE to save API calls
    # Note: We must deep copy this deck for each game! 
    # Current engine.start_game modifies the deck list in place?
    # Engine.start_game takes a list of Cards.
    # Our scryfall fetcher returns NEW instances now (model_copy).
    # But for 1000 sims, we should not fetch 1000 times.
    # We fetch once, then deep copy for each sim.
    
    base_deck, cmdr = await fetch_deck_from_decklist(deck_lines, commander_name)
    print(f"   Deck loaded: {len(base_deck)} cards. Commander: {cmdr}")
    
    stats = {
        "lands_turn_4": [],
        "mana_turn_4": [],
        "mana_turn_5": [],
        "permanents_turn_10": [],
        "deck_size_check": []
    }
    
    start_time = time.time()
    
    for i in range(num_sims):
        if i % 100 == 0:
            print(f"   Simulating game {i}...")
            
        # Create FRESH copies for this game
        # Card is Pydantic model, use model_copy(deep=True)
        game_deck = [c.model_copy(deep=True) for c in base_deck]
        
        engine = GameEngine(verbose=False) # Silent mode
        engine.start_game(game_deck, commander_name=cmdr)
        
        # Run turns
        for t in range(1, turns + 1):
            engine.step()
            
            # Snapshots
            if t == 4:
                stats["lands_turn_4"].append(len([c for c in engine.state.battlefield if c.is_land]))
                # Mana could be calculated by tapping out? Or just known resources
                # Heuristic heuristic: lands + mana rocks
                mana_sources = len([c for c in engine.state.battlefield if c.is_land or ("MANA_ROCK" in c.tags and "TAPPED_ENTRY" not in c.tags)])
                stats["mana_turn_4"].append(mana_sources)
            
            if t == 5:
                 mana_sources = len([c for c in engine.state.battlefield if c.is_land or ("MANA_ROCK" in c.tags)])
                 stats["mana_turn_5"].append(mana_sources)
        
        stats["permanents_turn_10"].append(len(engine.state.battlefield))
        stats["deck_size_check"].append(len(engine.state.library) + len(engine.state.hand) + len(engine.state.battlefield) + len(engine.state.graveyard))

    duration = time.time() - start_time
    print(f"\n✅ Simulation complete in {duration:.2f}s ({(duration/num_sims)*1000:.2f}ms/game)")
    
    # Analysis
    avg_lands_t4 = statistics.mean(stats["lands_turn_4"])
    avg_mana_t5 = statistics.mean(stats["mana_turn_5"])
    avg_deck_size = statistics.mean(stats["deck_size_check"])
    
    print("\n📊 Results:")
    print(f"   Average Lands on Turn 4: {avg_lands_t4:.2f}")
    print(f"   Average Mana Sources Turn 5: {avg_mana_t5:.2f}")
    print(f"   Deck Size Integrity check: {avg_deck_size:.1f} (Should be 99 + 1 in command zone = 100ish?)") 
    # Note: Commander is in Command Zone? Engine doesn't track Command Zone explicitly yet, just removes from deck.
    # So deck size should be 99.
    
    print("\n   Consistency Check (Turn 4 Lands):")
    # Histogram
    dist = defaultdict(int)
    for n in stats["lands_turn_4"]:
        dist[n] += 1
    for k in sorted(dist.keys()):
        bar = "#" * (dist[k] // (num_sims // 50)) # Scale for display
        print(f"   {k} Lands: {dist[k]} ({dist[k]/num_sims*100:.1f}%) {bar}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MTG Commander Monte Carlo Sim")
    parser.add_argument("--sims", type=int, default=100, help="Number of simulations")
    parser.add_argument("--turns", type=int, default=10, help="Turns per game")
    parser.add_argument("--deck", type=str, default="data/sample_decklist.txt", help="Deck file")
    args = parser.parse_args()
    
    with open(args.deck, "r") as f:
        lines = f.readlines()
    
    # Basic commander extraction if not provided (assume line in file)
    # Our updated fetch_deck_from_decklist handles it.
    
    asyncio.run(run_simulation(lines, None, args.sims, args.turns))
