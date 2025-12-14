"""Game engine for Goldfish simulation (solo playtesting)."""

import random
from typing import Optional
from .models import Card


class GameState:
    """
    Tracks the complete game state for a Goldfish simulation.
    
    Zones:
        - library: Undrawn cards
        - hand: Cards in hand
        - battlefield: Permanents in play
        - graveyard: Dead/discarded cards
    
    Resources:
        - mana_pool: Available mana by color
        - turn_counter: Current turn number
        - land_played_this_turn: Whether a land has been played this turn
    """
    
    def __init__(self):
        """Initialize empty game state."""
        # Zones
        self.library: list[Card] = []
        self.hand: list[Card] = []
        self.battlefield: list[Card] = []
        self.graveyard: list[Card] = []
        
        # Resources
        self.mana_pool: dict[str, int] = {}
        self.turn_counter: int = 0
        self.land_played_this_turn: Optional[Card] = None  # Track specific land card
        self.cards_played_this_turn: list[Card] = []  # Track all cards played for sickness/tapped checks
        
        # Commander zone (set aside)
        self.commander: Optional[Card] = None
    
    def draw_card(self) -> Optional[Card]:
        """
        Draw a card from library to hand.
        
        Returns:
            The drawn card, or None if library is empty
        """
        if not self.library:
            return None
        
        card = self.library.pop(0)
        self.hand.append(card)
        return card
    
    def play_land(self, card: Card) -> bool:
        """
        Play a land from hand to battlefield.
        
        Args:
            card: Land card to play
        
        Returns:
            True if successful, False if land already played or card not in hand
        """
        if self.land_played_this_turn:
            return False
        
        if card not in self.hand:
            return False
        
        if not card.is_land:
            return False
        
        self.hand.remove(card)
        self.battlefield.append(card)
        self.land_played_this_turn = card  # Store reference to the land
        self.cards_played_this_turn.append(card)
        return True
    
    def cast_spell(self, card: Card, mana_cost: dict[str, int]) -> bool:
        """
        Cast a spell from hand.
        
        Permanents (Artifact, Creature, etc.) go to battlefield.
        Spells (Instant, Sorcery) go to graveyard after casting.
        
        Args:
            card: Card to cast
            mana_cost: Mana cost to pay
        
        Returns:
            True if successful, False if card not in hand or insufficient mana
        """
        if card not in self.hand:
            return False
        
        # Check if we can afford it
        if not self.can_afford(mana_cost):
            # CRITICAL: This should never happen if logic is correct
            raise ValueError(
                f"Cannot afford spell {card.name} (Cost: {mana_cost}). "
                f"Pool: {self.mana_pool}"
            )
            return False
        
        # Pay the cost
        for color, amount in mana_cost.items():
            self.mana_pool[color] = self.mana_pool.get(color, 0) - amount
        
        # Remove from hand
        self.hand.remove(card)
        
        # Permanents go to battlefield, spells go to graveyard
        if card.is_permanent:
            self.battlefield.append(card)
            self.cards_played_this_turn.append(card)
        else:
            # Instant/Sorcery goes directly to graveyard
            self.graveyard.append(card)
            # Spells on stack technically "played" but don't persist, tracking for completeness if needed
        
        return True
    
    def add_mana(self, mana: dict[str, int]):
        """
        Add mana to the mana pool.
        
        Args:
            mana: Mana to add (e.g., {"colorless": 1} or {"R": 1, "G": 1})
        """
        for color, amount in mana.items():
            self.mana_pool[color] = self.mana_pool.get(color, 0) + amount
    
    def clear_mana_pool(self):
        """Clear all mana from the mana pool (end of turn)."""
        self.mana_pool = {}
        self.cards_played_this_turn = []
    
    def can_afford(self, cost: dict[str, int]) -> bool:
        """
        Check if we can afford a mana cost.
        
        For Phase 2 simplification: all mana is colorless, so just check total.
        
        Args:
            cost: Mana cost to check
        
        Returns:
            True if we have enough mana
        """
        total_cost = sum(cost.values())
        total_available = sum(self.mana_pool.values())
        return total_available >= total_cost
    
    def get_total_mana(self) -> int:
        """Get total mana available in pool."""
        return sum(self.mana_pool.values())
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return (
            f"Turn {self.turn_counter}\n"
            f"  Hand: {len(self.hand)} cards\n"
            f"  Battlefield: {len(self.battlefield)} permanents\n"
            f"  Library: {len(self.library)} cards\n"
            f"  Mana: {self.get_total_mana()}"
        )


class GameEngine:
    """
    Manages game flow for Goldfish simulation.
    
    A "Goldfish" game simulates playing against an imaginary opponent who does nothing,
    allowing us to test how well a deck can execute its game plan.
    """
    
    def __init__(self, verbose: bool = False, export_mode: str = "detailed"):
        """
        Initialize game engine.
        
        Args:
            verbose: If True, print detailed turn-by-turn logs
            export_mode: "detailed" (default) saves logs to json, "summary" skips logs for speed
        """
        self.state = GameState()
        self.verbose = verbose
        self.export_mode = export_mode
        self.game_log: list[dict] = []  # Track all game events for export
        
        # Monte Carlo specific stats
        self._mc_stats = {
            "mana_turn_4": 0,
            "lands_turn_4": 0, # Pure land count for verification
            "hand_empty_turn": None,
            "final_lands": 0,
            "final_turn": 0
        }
    
    def _log_event(self, event_type: str, details: dict):
        """
        Log a game event for later export.
        
        Args:
            event_type: Type of event (e.g., "draw", "play_land", "cast_spell")
            details: Event details
        """
        if self.export_mode == "detailed":
            event = {
                "turn": self.state.turn_counter,
                "event": event_type,
                **details
            }
            self.game_log.append(event)
    
    def start_game(self, deck: list[Card], commander: Optional[Card] = None):
        """
        Start a new game with the given deck.
        
        Args:
            deck: 99-card deck (or 100 if no commander specified)
            commander: Optional commander card (if None, auto-detect from deck)
        """
        # Use provided commander or auto-detect
        if commander is None:
            # Separate commander (assume first legendary creature)
            for card in deck:
                if "Legendary" in card.type_line and "Creature" in card.type_line:
                    commander = card
                    break
        
        # Remove commander from deck if found
        library = [c for c in deck if c != commander]
        
        # If still no commander, just use all cards as library
        if commander is None and deck:
            library = deck
        
        self.state.commander = commander
        self.state.library = library.copy()
        
        # Shuffle library
        import random
        import time
        # Ensure true randomness (default is system time, but being explicit helps)
        random.seed(None) 
        random.shuffle(self.state.library)
        # Double shuffle for good luck (and to reassure user)
        random.shuffle(self.state.library)
        
        if self.verbose:
            print(f"   Library: {len(self.state.library)} cards")
            
        # Draw opening hand (7 cards)
        opening_hand = []
        for _ in range(7):
            card = self.state.draw_card()
            if card:
                opening_hand.append(card)
        
        # Log opening hand
        self._log_event("opening_hand", {
            "cards": [{"name": c.name, "cmc": c.cmc, "is_land": c.is_land} for c in opening_hand],
            "hand_size": len(opening_hand),
            "lands_in_hand": len([c for c in opening_hand if c.is_land]),
        })
        
        # Start at turn 1
        self.state.turn_counter = 1
        
        if self.verbose:
            print("🎮 Game started!")
            print(f"   Commander: {commander.name if commander else 'None'}")
            print(f"   Library: {len(self.state.library)} cards")
            print(f"   Opening hand: {len(self.state.hand)} cards")
            if opening_hand:
                print(f"   Cards in hand:")
                for card in opening_hand:
                    land_marker = " 🟢" if card.is_land else ""
                    print(f"     - {card.name} (CMC {card.cmc}){land_marker}")
    
    def step(self):
        """
        Execute one complete turn using greedy heuristic.
        
        Turn structure:
        1. Untap phase (future: untap permanents)
        2. Upkeep phase (future: triggered abilities)
        3. Draw phase
        4. Main phase (play cards using heuristic)
        5. End phase (cleanup)
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Turn {self.state.turn_counter}")
            print(f"{'='*60}")
        
        # Log turn start
        self._log_event("turn_start", {
            "hand_size": len(self.state.hand),
            "battlefield_size": len(self.state.battlefield),
            "library_size": len(self.state.library),
        })
        
        # 1. Untap phase & Upkeep
        # In Phase 2 (Goldfish), we assume everything untaps.
        # Log untap step showing what became available
        lands_on_battlefield = [c for c in self.state.battlefield if c.is_land]
        mana_rocks = [c for c in self.state.battlefield if "RAMP" in c.tags and "ARTIFACT" in c.tags]
        
        self._log_event("untap_step", {
            "untapped_lands": len(lands_on_battlefield),
            "untapped_artifacts": len(mana_rocks),
            "total_permanents": len(self.state.battlefield)
        })
        
        # 3. Draw phase
        drawn = self.state.draw_card()
        if drawn:
            self._log_event("draw", {"card": drawn.name, "cmc": drawn.cmc})
            if self.verbose:
                print(f"📥 Drew: {drawn.name}")
        
        # 4. Main phase - greedy heuristic
        self._main_phase_heuristic()
        
        # 5. End phase
        self.state.clear_mana_pool()
        self.state.land_played_this_turn = None
        
        # Log turn end
        self._log_event("turn_end", {
            "hand_size": len(self.state.hand),
            "battlefield_size": len(self.state.battlefield),
            "lands_on_battlefield": len([c for c in self.state.battlefield if c.is_land]),
            "mana_pool_remaining": self.state.get_total_mana() # Should be 0
        })
        
        self.state.turn_counter += 1
        
        if self.verbose:
            print(f"\n📊 End of turn:")
            print(f"   Battlefield: {len(self.state.battlefield)} permanents")
            print(f"   Hand: {len(self.state.hand)} cards")
            print(f"   Library: {len(self.state.library)} cards")

        # UPDATE STATS (Monte Carlo)
        # Turn 4 Mana ends -> capture state
        if self.state.turn_counter == 5: 
             # We just finished Turn 4 (counter increments at end of loop).
             # Calculate available mana sources
             lands = len([c for c in self.state.battlefield if c.is_land])
             rocks = len([c for c in self.state.battlefield if "MANA_ROCK" in c.tags])
             self._mc_stats["mana_turn_4"] = lands + rocks
             self._mc_stats["lands_turn_4"] = lands
        
        # Empty Hand Check
        if not self.state.hand and self._mc_stats["hand_empty_turn"] is None:
             self._mc_stats["hand_empty_turn"] = self.state.turn_counter - 1

    def run_simulation(self, turns: int = 20) -> dict:
        """
        Run a full simulation and return results.
        
        Args:
            turns: Number of turns to simulate
            
        Returns:
            Dictionary with simulation summary
        """
        self.run_turns(turns)
        
        # Finalize stats
        self._mc_stats["final_turn"] = self.state.turn_counter - 1
        self._mc_stats["final_lands"] = len([c for c in self.state.battlefield if c.is_land])
        
        return self._mc_stats    
    def _check_enters_tapped(self, card: Card) -> bool:
        """
        Check if a land enters tapped based on game state.
        
        Args:
            card: The land card being played
            
        Returns:
            True if it enters tapped, False otherwise.
        """
        if "TAPPED_ENTRY" not in card.tags:
            return False
            
        # Check conditions that might UNTAP it
        
        # 1. Fastlands: "unless you control two or fewer other lands"
        if "COND_FASTLAND" in card.tags:
            # Count other lands
            lands = len([c for c in self.state.battlefield if c.is_land and c != card])
            # Note: "two or fewer OTHER lands".
            # If we call this AFTER adding to battlefield, we must subtract 1 (itself).
            # The engine logic adds to battlefield THEN logs.
            # If card is already on battlefield:
            if card in self.state.battlefield:
                # lands var above already excludes 'card' via filter
                pass
            else:
                # Predicting before add
                pass
                
            if lands <= 2:
                return False
                
        # 2. Count Checklands (Dwarven Mine): "unless you control 3 or more Mountains"
        # Tag format: COND_COUNT_3_MOUNTAIN
        for tag in card.tags:
            if tag.startswith("COND_COUNT_3_"):
                land_type = tag.split("_")[-1].capitalize() # MOUNTAIN -> Mountain
                # Count lands with subtype
                count = 0
                for c in self.state.battlefield:
                    if c.is_land and c != card and land_type in c.type_line:
                        count += 1
                
                if count >= 3:
                    return False
        
        return True

    def _main_phase_heuristic(self):
        """
        Simple greedy heuristic for main phase:
        1. Play a land if available
        2. Tap all UNTAPPED lands for mana
        3. Cast most expensive affordable spell
        4. Repeat step 3 until no spells can be cast
        """
        # Step 1: Play a land
        lands_in_hand = [card for card in self.state.hand if card.is_land]
        if lands_in_hand and not self.state.land_played_this_turn:
            land = lands_in_hand[0]  # Just play first land
            self.state.play_land(land)
            
            enters_tapped = self._check_enters_tapped(land)
            
            self._log_event("play_land", {
                "card": land.name,
                "enters_tapped": enters_tapped
            })
            if self.verbose:
                tapped_marker = " (enters tapped)" if enters_tapped else ""
                print(f"🌳 Played land: {land.name}{tapped_marker}")
        
        # Step 2 & 3: Dynamic Loop (Tap -> Cast -> Tap -> Cast ...)
        # This allows using mana rocks (like Sol Ring) immediately after casting them
        
        # Track objects tapped this turn/phase to prevent double dipping
        # Note: Since we only do main phase in Phase 2, this acts as "Tapped status"
        tapped_objects = set() 
        
        while True:
            mana_added_this_loop = False
            
            # Lands
            lands_on_battlefield = [c for c in self.state.battlefield if c.is_land]
            untapped_lands = []
            for land in lands_on_battlefield:
                if id(land) in tapped_objects:
                    continue
                
                # Check eligibility
                # Logic: Is it valid source?
                
                # CRITICAL: Fetch Lands (Evolving Wilds) generally do NOT produce mana.
                if "FETCH_LAND" in land.tags:
                    continue
                
                # Check if it entered tapped this turn (e.g. Fetched Land, Evolving Wilds itself)
                # We must check ALL cards played this turn, not just property land_played_this_turn
                if land in self.state.cards_played_this_turn and "TAPPED_ENTRY" in land.tags:
                     continue
                     
                # Fallback: Special check for the played land if tags missing for some reason (shouldn't happen with updated logic)
                if land == self.state.land_played_this_turn:
                     if self._check_enters_tapped(land):
                          continue
                
                untapped_lands.append(land)
        
            for land in untapped_lands:
                self.state.add_mana({"colorless": 1})
                tapped_objects.add(id(land))
                mana_added_this_loop = True
            
            # Artifacts (Mana Rocks)
            # Use MANA_ROCK tag to distinguish from generic RAMP (like Wayfarer's Bauble)
            mana_rocks = [c for c in self.state.battlefield if "MANA_ROCK" in c.tags and "ARTIFACT" in c.tags]
            active_artifacts = {}
            for artifact in mana_rocks:
                if id(artifact) in tapped_objects:
                    continue

                # Check eligibility (Summoning Sickness / Tapped Entry)
                if artifact in self.state.cards_played_this_turn:
                    # Generic check for any permanent entered tapped
                    if "TAPPED_ENTRY" in artifact.tags:
                        continue
                    # If it's a creature, assume summoning sickness (no haste support yet)
                    if "Creature" in artifact.type_line:
                        continue
                
                self.state.add_mana({"colorless": 1})
                tapped_objects.add(id(artifact))
                active_artifacts[artifact.name] = active_artifacts.get(artifact.name, 0) + 1
                mana_added_this_loop = True
                
            # Log generation (initial only? No, log incremental?)
            # The original design logged ONCE.
            # We should probably aggregate or log increments.
            # For simplicity avoiding spam: Log only if we added mana AND it's the first pass?
            # Or log "generate_mana" events incrementally.
            if mana_added_this_loop:
                 total_mana = self.state.get_total_mana()
                 # Only log if we generated significant mana or verbose?
                 # Actually the previous log logic was per turn.
                 # Let's log incremental generation events.
                 if active_artifacts or untapped_lands:
                     self._log_event("generate_mana", {
                        "available_mana_from_permanents": total_mana,
                        "sources": {"lands": len(untapped_lands), "artifacts": active_artifacts}
                     })
                     if self.verbose and (len(untapped_lands) > 0 or active_artifacts):
                        artifact_str = f", Artifacts: {active_artifacts}" if active_artifacts else ""
                        print(f"💎 Generated incremental mana (Lands: {len(untapped_lands)}{artifact_str})")

            # Cast Spells
            spell_cast_this_loop = False
            
            # Find affordable spells
            non_land_cards = [c for c in self.state.hand if not c.is_land]
            affordable = [c for c in non_land_cards if self.state.can_afford(c.mana_cost)]
            
            if affordable:
                affordable.sort(key=lambda c: c.cmc, reverse=True)
                spell = affordable[0]
                
                if self.state.cast_spell(spell, spell.mana_cost):
                    spell_cast_this_loop = True
                    self._log_event("cast_spell", {
                        "card": spell.name,
                        "cmc": spell.cmc,
                        "is_permanent": spell.is_permanent,
                        "mana_spent": sum(spell.mana_cost.values()),
                        "mana_remaining": self.state.get_total_mana(),
                    })
                    if self.verbose:
                         dest = "→ Battlefield" if spell.is_permanent else "→ Graveyard"
                         print(f"✨ Cast: {spell.name} (CMC {spell.cmc}) {dest}")
                    
                    # DYNAMIC MANA FIX (Sol Ring)
                    # Use MANA_ROCK tag
                    if spell.is_permanent and "MANA_ROCK" in spell.tags and "ARTIFACT" in spell.tags:
                        if "TAPPED_ENTRY" not in spell.tags:
                            # New mana source available! Tap it immediately.
                            # Logic handled by next loop iteration! 
                            # But logging helpful.
                            if self.verbose:
                                print(f"   ⚡ Tapped new {spell.name} for 1 mana (next loop)")
            
            # Break conditions
            if not mana_added_this_loop and not spell_cast_this_loop:
                # Try to crack Fetch Lands before giving up?
                # This could change available mana (unlikely, usually fetch land enters tapped)
                # But it changes deck composition (shuffle).
                if self._resolve_fetch_lands(tapped_objects):
                    # If we fetched, state changed (new land on battlefield).
                    # Loop again to see if we can use the new land (unlikely if tapped, but safe to loop).
                    continue
                
                break
    
    def _resolve_fetch_lands(self, tapped_objects: set) -> bool:
        """
        Check for and resolve available Fetch Lands (Evolving Wilds, etc.).
        
        Returns:
            True if a fetch occurred (state changed).
        """
        # Find potential fetch lands on battlefield
        fetchers = [c for c in self.state.battlefield if "FETCH_LAND" in c.tags]
        
        for fetcher in fetchers:
            # Check availability
            
            # Case 1: Activated Ability ("{T}, Sacrifice...")
            # Evolving Wilds, Terramorphic Expanse
            if "{T}" in fetcher.oracle_text:
                if id(fetcher) in tapped_objects:
                    continue # Already used or tapped
                if fetcher == self.state.land_played_this_turn and "TAPPED_ENTRY" in fetcher.tags:
                    continue # Enters tapped, cannot use {T} ability yet
            
            # Case 2: Triggered Ability ("When ... enters ... sacrifice it")
            # Brokers Hideout, Riveteers Overlook, etc.
            # Implicitly happens immediately upon entry. 
            # If it's on the battlefield, we haven't sacced it yet. do it now.
            
            # ACTION: Crack the fetch
            
            # 1. Sacrifice (Remove from battlefield, add to graveyard)
            self.state.battlefield.remove(fetcher)
            self.state.graveyard.append(fetcher)
            
            # 2. Search Library Logic
            # Heuristic: Find first "Basic" "Land".
            # If none, find any "Basic Land" (logic: greedy, just get a land).
            target_land = None
            for card in self.state.library:
                if card.is_land and ("Basic" in card.type_line or any(x in card.type_line for x in ["Mountain", "Island", "Plains", "Swamp", "Forest"])):
                     target_land = card
                     break
            
            if target_land:
                # 3. Move target to battlefield (TAPPED)
                self.state.library.remove(target_land)
                self.state.battlefield.append(target_land)
                self.state.cards_played_this_turn.append(target_land) # Summoning sickness / Tapped logic
                
                # Force TAPPED_ENTRY tag effectively for this turn
                # (Engine checks cards_played_this_turn. If it has TAPPED_ENTRY tag, it's tapped.
                # If basic land doesn't have tag, it might seem untapped?)
                # We need to track that it entered tapped. 
                # Simplest: Add TAPPED_ENTRY tag to the *instance* (Card is Pydantic, mutable in our flow).
                if "TAPPED_ENTRY" not in target_land.tags:
                    target_land.tags.append("TAPPED_ENTRY")
                
                # 4. Shuffle
                import random
                # random.seed(None) # Already reset at start
                random.shuffle(self.state.library)
                
                # Log
                self._log_event("activate_ability", {
                    "card": fetcher.name,
                    "effect": f"Fetched {target_land.name}",
                    "shuffle": True
                })
                if self.verbose:
                    print(f"   🌪️ Cracked {fetcher.name} -> Fetched {target_land.name} (tapped)")
                
                return True # State changed, restart loop
            else:
                 # Failed to find basic land?
                 if self.verbose:
                     print(f"   ⚠️ Cracked {fetcher.name} but found no Basic Land!")
                 return True # Still state changed (sacrificed)
                 
        return False
    
    def run_turns(self, n: int):
        """
        Run N turns of the game.
        
        Args:
            n: Number of turns to simulate
        """
        for _ in range(n):
            self.step()
    
    def get_summary(self) -> dict:
        """
        Get current game state summary.
        
        Returns:
            Dictionary with game statistics
        """
        return {
            "turn": self.state.turn_counter,
            "hand_size": len(self.state.hand),
            "battlefield_size": len(self.state.battlefield),
            "library_size": len(self.state.library),
            "lands_on_battlefield": len([c for c in self.state.battlefield if c.is_land]),
            "mana_available": self.state.get_total_mana(),
        }
    
    def export_log(self, filepath: str):
        """
        Export game log to JSON file.
        
        Creates a detailed JSON log with:
        - Game metadata (commander, deck size)
        - Turn-by-turn events (draw, play_land, cast_spell, etc.)
        - Final statistics
        
        Args:
            filepath: Path to save JSON file
        """
        import json
        from datetime import datetime
        
        log_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "commander": self.state.commander.name if self.state.commander else None,
                "total_turns": self.state.turn_counter - 1,
                "deck_size": len(self.state.library) + len(self.state.hand) + len(self.state.battlefield),
            },
            "events": self.game_log,
            "final_state": self.get_summary(),
        }
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
