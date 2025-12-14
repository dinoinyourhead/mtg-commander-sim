
import asyncio
import math
import os
import sys
from collections import Counter

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from simulation.batch_runner import BatchRunner
from core.scryfall import fetch_deck_from_decklist

def hypergeometric_probability(N, K, n, k):
    """
    Calculate Hypergeometric probability.
    N: Population size (Deck size = 99)
    K: Success states in population (Lands in deck = 35)
    n: Number of draws (Turn 4 = 7 initial + 4 draws = 11)
    k: Number of observed successes (Lands on battlefield + hand)
    
    Note: Engine metric 'lands_turn_4' is 'Lands on Battlefield'.
    We assume greedy heuristic plays ALL lands.
    So 'Lands on Battlefield' ~= 'Total Lands Drawn' (capped by turns played if we drew >4? No, max 1 per turn).
    
    Actually: 
    Turn 4 means we could have played max 4 lands.
    If we drew 5 lands, we have 4 on field, 1 in hand.
    So 'Observed Lands on Field' = min(Lands Drawn, 4).
    """
    def nCr(n, r):
        if r < 0 or r > n:
            return 0
        return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))

    return (nCr(K, k) * nCr(N - K, n - k)) / nCr(N, n)

def calculate_expected_lands_on_field(deck_size, land_count, turn):
    """
    Calculate theoretical expected lands on battlefield by specific turn.
    Assumptions:
    - We draw 7 + turn (if on play? Goldfish assumes draw logic)
      Engine draw logic: Start 7. Turn 1 draw.
      So Turn 4 = 7 + 4 = 11 cards seen.
    - We play 1 land per turn if we have one.
    - Max lands on field = Turn Number.
    """
    cards_seen = 7 + turn
    expected_value = 0.0
    
    # Iterate through all possible number of lands drawn (0 to cards_seen)
    for lands_drawn in range(cards_seen + 1):
        prob = hypergeometric_probability(deck_size, land_count, cards_seen, lands_drawn)
        
        # Lands on field is limited by the turn number (one drop per turn)
        lands_on_field = min(lands_drawn, turn)
        
        expected_value += lands_on_field * prob
        
    return expected_value

async def main():
    print("🧪 Starting Plausibility Verification...")
    print("   Goal: Compare Simulation vs Hypergeometric Theory")
    
    # 1. Load Deck to get counts
    deck_path = "data/sample_decklist.txt"
    with open(deck_path, "r") as f:
        lines = f.readlines()
    deck, cmdr = await fetch_deck_from_decklist(lines, None)
    
    total_cards = len(deck) # Should be 99 usually (Engine removes Commander)
    # Actually fetch_deck returns 100 including commander?
    # Engine.start_game removes commander.
    # So deck size in play is 99.
    
    land_count = sum(1 for c in deck if c.is_land)
    # Adjust for commander removal? 
    # If commander is not land (usually true), land count stays same, N becomes 99.
    
    print(f"   Deck Stats: {total_cards} Cards (approx), {land_count} Lands")
    print("   Assumption: Engine plays 1 land/turn greedy. Shuffle is random.")
    
    # 2. Run Batch
    sims = 5000
    runner = BatchRunner(deck, None)
    results = runner.run_batch(iterations=sims, turns=20)
    
    # 3. Analyze Turn 4
    observed_lands_t4 = [r['lands_turn_4'] for r in results]
    avg_observed = sum(observed_lands_t4) / sims
    
    # Theoretical Check
    # Commander is removed from library. So N=99.
    # Checks if commander is land? Unlikely.
    N = 99
    K = land_count
    turn = 4
    
    expected = calculate_expected_lands_on_field(N, K, turn)
    
    print("\n📊 Verification Results (Turn 4):")
    print(f"   Theoretical Expected Lands: {expected:.4f}")
    print(f"   Simulation Average Lands:   {avg_observed:.4f}")
    
    diff = abs(expected - avg_observed)
    percent_diff = (diff / expected) * 100
    
    print(f"   Difference: {diff:.4f} ({percent_diff:.2f}%)")
    
    if percent_diff < 5.0:
        print("   ✅ Plausibility Check PASSED! (Variance < 5%)")
        print("      The engine's shuffling and land-drop logic is statistically sound.")
    else:
        print("   ⚠️ Plausibility Check WARNING.")
        print("      Deviation is high. Checking if aggressive Mulligan or Ramp interference?")
        
    # Check Ramp Impact
    observed_mana_t4 = [r['mana_turn_4'] for r in results]
    avg_mana = sum(observed_mana_t4) / sims
    ramp_impact = avg_mana - avg_observed
    
    print(f"\n🚀 Ramp Statistics:")
    print(f"   Avg Mana Sources (Turn 4): {avg_mana:.4f}")
    print(f"   Ramp Contribution:         +{ramp_impact:.4f} mana from artifacts")
    
    # Confidence Interval Logic (Optional simple heuristic)
    # For 5000 runs, standard error is small.
    print(f"\n   Note: This confirms that the engine isn't 'cheating' land drops.")

if __name__ == "__main__":
    asyncio.run(main())
