
import multiprocessing
import time
import csv
from datetime import datetime
import os
import sys

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from core.engine import GameEngine
from core.models import Card

def _run_single_simulation(args):
    """
    Helper function for multiprocessing. 
    Args must be a tuple: (deck_list, commander_name, turns)
    """
    deck, commander, turns = args
    
    # Create FRESH copies for this game (Multiprocessing might serialize copies, but to be safe)
    # Actually multiprocessing pickles the args. 
    # But Card is a Pydantic model. Pickling should work.
    
    # We need to construct the deck instances inside the process if we want to be 100% safe
    # OR we assume the list passed in is deep copied by pickle during fork.
    # Python multiprocessing (spawn/fork) generally copies data.
    # However, to avoid any shared state issues with tags/mutable fields:
    # We will trust pickling.
    
    engine = GameEngine(verbose=False, export_mode="summary")
    
    # We might receive Cards or just data? 
    # Providing full Card objects is heavy for pickle?
    # 100 cards * 10k iterations.
    # Better: Pass the 'deck' as list of Card objects ONCE to the worker? 
    # Pool.map passes args.
    
    # Optimization: To avoid pickling 100 cards (complex objects) 10000 times,
    # we can use a global initializer or just pass lightweight data?
    # But `engine.start_game` needs `Card` objects.
    # Let's try passing the objects. 100 cards is small enough.
    
    # Explicitly model_copy just in case
    game_deck = [c.model_copy(deep=True) for c in deck]
    
    engine.start_game(game_deck, commander=commander)
    result = engine.run_simulation(turns=turns)
    return result

class BatchRunner:
    def __init__(self, deck: list[Card], commander: Card = None):
        self.deck = deck
        self.commander = commander

    def run_batch(self, iterations: int = 1000, turns: int = 20, processes: int = None) -> list[dict]:
        """
        Run N simulations in parallel.
        """
        if processes is None:
            processes = max(1, multiprocessing.cpu_count() - 1)
            
        print(f"🚀 Starting Batch Run: {iterations} games on {processes} cores...")
        start_time = time.time()
        
        # Prepare arguments
        # We must clone the deck for cleanliness, but pickling does that.
        # We pass the same 'base deck' to all.
        args = [(self.deck, self.commander, turns) for _ in range(iterations)]
        
        with multiprocessing.Pool(processes=processes) as pool:
            # map_async or starmap?
            # We wrapped args in tuple, so map works.
            results = pool.map(_run_single_simulation, args)
            
        duration = time.time() - start_time
        print(f"✅ Batch complete in {duration:.2f}s ({(duration/iterations)*1000:.2f}ms/game)")
        
        return results

    def save_results(self, results: list[dict], output_dir: str = "logs"):
        """Save results to CSV."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"monte_carlo_results_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        if not results:
            print("⚠️ No results to save.")
            return

        # Get headers from first result
        headers = results[0].keys()
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(results)
            
        print(f"💾 Results saved to: {filepath}")
        
    def print_summary(self, results: list[dict]):
        """Print console summary."""
        if not results:
            return
            
        total = len(results)
        
        # Calculate averages
        avg_mana_t4 = sum(r['mana_turn_4'] for r in results) / total
        avg_lands_end = sum(r['final_lands'] for r in results) / total
        
        # Empty hand stats
        empty_hand_games = [r['hand_empty_turn'] for r in results if r['hand_empty_turn'] is not None]
        avg_empty_turn = sum(empty_hand_games) / len(empty_hand_games) if empty_hand_games else 0.0
        pct_empty = (len(empty_hand_games) / total) * 100
        
        print("\n📊 Monte Carlo Summary:")
        print(f"   Games Played: {total}")
        print(f"   Avg Mana (Turn 4): {avg_mana_t4:.2f}")
        print(f"   Avg Lands (End):   {avg_lands_end:.2f}")
        print(f"   Empty Hand:        {pct_empty:.1f}% (Avg Turn: {avg_empty_turn:.1f})")

if __name__ == "__main__":
    import argparse
    import asyncio
    from core.scryfall import fetch_deck_from_decklist
    
    async def main():
        parser = argparse.ArgumentParser(description="MTG Commander Monte Carlo Batch Runner")
        parser.add_argument("--sims", type=int, default=1000, help="Number of simulations to run")
        parser.add_argument("--turns", type=int, default=20, help="Number of turns per game")
        parser.add_argument("--deck", type=str, default="data/sample_decklist.txt", help="Path to decklist file")
        parser.add_argument("--processes", type=int, default=None, help="Number of CPU cores to use (default: max - 1)")
        
        args = parser.parse_args()
        
        if not os.path.exists(args.deck):
            print(f"❌ Deck file not found: {args.deck}")
            return
            
        print(f"📥 Loading deck from {args.deck}...")
        with open(args.deck, "r") as f:
            lines = f.readlines()
            
        deck, cmdr = await fetch_deck_from_decklist(lines, None)
        
        runner = BatchRunner(deck, None) # Let engine find commander by name/type
        results = runner.run_batch(iterations=args.sims, turns=args.turns, processes=args.processes) 
        
        runner.save_results(results)
        runner.print_summary(results)

    asyncio.run(main())
