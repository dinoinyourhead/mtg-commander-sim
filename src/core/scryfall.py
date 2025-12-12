"""Scryfall API client for fetching card data."""

import asyncio
import re
from typing import Optional
import httpx

from .models import Card
from .tags import assign_tags


# Scryfall API base URL
SCRYFALL_API_BASE = "https://api.scryfall.com"

# Rate limiting: Scryfall requests 50-100ms between requests
RATE_LIMIT_DELAY = 0.1  # 100ms


def parse_mana_cost(mana_cost_str: str) -> dict[str, int]:
    """
    Parse Scryfall mana cost string into dictionary format.
    
    Example: "{2}{R}{G}" -> {"colorless": 2, "R": 1, "G": 1}
    
    Args:
        mana_cost_str: Mana cost string from Scryfall (e.g., "{2}{R}{G}")
    
    Returns:
        Dictionary with mana symbols as keys and counts as values
    """
    if not mana_cost_str:
        return {}
    
    # Extract all mana symbols from {X} format
    symbols = re.findall(r"\{([^}]+)\}", mana_cost_str)
    
    mana_dict: dict[str, int] = {}
    
    for symbol in symbols:
        # Handle generic/colorless mana (numbers)
        if symbol.isdigit():
            colorless = int(symbol)
            mana_dict["colorless"] = mana_dict.get("colorless", 0) + colorless
        # Handle hybrid mana like {R/G}
        elif "/" in symbol:
            # For simplicity, count hybrid as first color
            color = symbol.split("/")[0]
            mana_dict[color] = mana_dict.get(color, 0) + 1
        # Handle Phyrexian mana like {R/P}
        elif "/P" in symbol:
            color = symbol.split("/")[0]
            mana_dict[color] = mana_dict.get(color, 0) + 1
        # Handle X, Y, Z
        elif symbol in ["X", "Y", "Z"]:
            mana_dict["X"] = mana_dict.get("X", 0) + 1
        # Standard color symbols (W, U, B, R, G, C)
        else:
            mana_dict[symbol] = mana_dict.get(symbol, 0) + 1
    
    return mana_dict


def parse_card_name(line: str) -> Optional[str]:
    """
    Parse a card name from various decklist formats.
    
    Handles:
    - Plain names: "Sol Ring"
    - With quantity: "1 Sol Ring", "3x Forest"
    - With set codes: "1 Sol Ring (CMD)"
    
    Args:
        line: Line from decklist file
    
    Returns:
        Clean card name, or None if line is empty/invalid
    """
    line = line.strip()
    if not line:
        return None
    
    # Remove quantity prefix (e.g., "1 ", "3x ", "1x ")
    # Matches: "1 Sol Ring", "3x Forest", "1x Command Tower"
    line = re.sub(r"^\d+x?\s+", "", line)
    
    # Remove set codes in parentheses (e.g., "Sol Ring (CMD)")
    line = re.sub(r"\s*\([^)]+\)\s*$", "", line)
    
    return line.strip() if line.strip() else None


async def fetch_card_from_scryfall(
    card_name: str,
    client: httpx.AsyncClient,
    retry_count: int = 0,
    max_retries: int = 5,
    cache: Optional['ScryfallCache'] = None
) -> Optional[dict]:
    """
    Fetch a single card from Scryfall API by name with exponential backoff.
    
    Handles HTTP 429 (Too Many Requests) with exponential backoff to prevent IP bans.
    Scryfall documentation: "Excessive requests may result in temporary or permanent ban"
    
    Uses cache if provided to reduce API calls.
    
    Args:
        card_name: Name of the card to fetch
        client: httpx AsyncClient instance
        retry_count: Current retry attempt (internal use)
        max_retries: Maximum number of retries for rate limiting
        cache: Optional ScryfallCache for caching responses
    
    Returns:
        Scryfall card data as dict, or None if not found
    """
    # Check cache first
    if cache:
        cached_data = cache.get(card_name)
        if cached_data:
            return cached_data
    
    url = f"{SCRYFALL_API_BASE}/cards/named"
    params = {"fuzzy": card_name}
    
    try:
        response = await client.get(url, params=params)
        
        if response.status_code == 200:
            card_data = response.json()
            # Cache successful response
            if cache:
                cache.put(card_name, card_data)
            return card_data
        
        elif response.status_code == 404:
            print(f"⚠️  Card not found: {card_name}")
            return None
        
        elif response.status_code == 429:
            # Rate limited! Implement exponential backoff
            if retry_count >= max_retries:
                print(f"❌ Rate limit exceeded after {max_retries} retries for: {card_name}")
                return None
            
            # Exponential backoff: 2^retry * base_delay
            # Retry 1: 2s, Retry 2: 4s, Retry 3: 8s, Retry 4: 16s, Retry 5: 32s
            backoff_delay = (2 ** retry_count) * 1.0
            
            print(f"⚠️  Rate limited (HTTP 429)! Waiting {backoff_delay:.1f}s before retry {retry_count + 1}/{max_retries}...")
            await asyncio.sleep(backoff_delay)
            
            # Recursive retry
            return await fetch_card_from_scryfall(card_name, client, retry_count + 1, max_retries, cache)
        
        else:
            print(f"⚠️  Error fetching {card_name}: HTTP {response.status_code}")
            return None
    
    except Exception as e:
        print(f"⚠️  Exception fetching {card_name}: {e}")
        return None



def create_card_from_scryfall_data(card_data: dict) -> Card:
    """
    Create a Card object from Scryfall API response.
    
    Args:
        card_data: Raw Scryfall card data
    
    Returns:
        Card instance with tags applied
    """
    name = card_data.get("name", "Unknown")
    mana_cost_str = card_data.get("mana_cost", "")
    cmc = int(card_data.get("cmc", 0))
    type_line = card_data.get("type_line", "")
    oracle_text = card_data.get("oracle_text", "")
    scryfall_id = card_data.get("id", "")
    color_identity = card_data.get("color_identity", [])
    
    # Parse mana cost
    mana_cost = parse_mana_cost(mana_cost_str)
    
    # Assign tags
    tags = assign_tags(name, type_line, oracle_text)
    
    return Card(
        name=name,
        mana_cost=mana_cost,
        cmc=cmc,
        type_line=type_line,
        oracle_text=oracle_text,
        tags=tags,
        scryfall_id=scryfall_id,
        color_identity=color_identity,
    )


async def fetch_cards(card_names: list[str], use_cache: bool = True) -> list[Card]:
    """
    Fetch multiple cards from Scryfall API.
    
    This is the main entry point for card fetching. It handles:
    - Parsing card names from various formats (plain, with quantities, etc.)
    - Caching (24h TTL) to reduce API calls
    - Rate limiting (100ms between requests)
    - Exponential backoff on HTTP 429 (rate limiting)
    - Error handling for missing cards
    - Automatic tagging
    
    Args:
        card_names: List of card names to fetch (supports formats like "1 Sol Ring")
        use_cache: Whether to use cache (default: True)
    
    Returns:
        List of Card objects (may be shorter than input if some cards not found)
    """
    from .cache import ScryfallCache
    
    cards: list[Card] = []
    
    # Initialize cache
    cache = ScryfallCache() if use_cache else None
    
    if cache:
        # Clear expired entries
        expired = cache.clear_expired()
        if expired > 0:
            print(f"🧹 Cleared {expired} expired cache entries")
    
    # Parse and clean card names
    cleaned_names = []
    for name in card_names:
        parsed = parse_card_name(name)
        if parsed:
            cleaned_names.append(parsed)
    
    # Track cache hits/misses
    cache_hits = 0
    cache_misses = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, card_name in enumerate(cleaned_names):
            # Check if in cache (already checked in fetch_card_from_scryfall, but track stats)
            if cache and cache.get(card_name):
                cache_hits += 1
            else:
                cache_misses += 1
            
            # Rate limiting: wait between requests (only for cache misses)
            if i > 0 and not (cache and cache.get(card_name)):
                await asyncio.sleep(RATE_LIMIT_DELAY)
            
            card_data = await fetch_card_from_scryfall(card_name, client, cache=cache)
            
            if card_data:
                card = create_card_from_scryfall_data(card_data)
                cards.append(card)
    
    # Show cache stats
    if cache:
        print(f"💾 Cache: {cache_hits} hits, {cache_misses} misses ({cache_hits/(cache_hits+cache_misses)*100:.1f}% hit rate)")
    
    return cards


def parse_decklist(lines: list[str]) -> tuple[list[tuple[str, int]], Optional[str]]:
    """
    Parse a decklist and extract (card_name, quantity) tuples plus commander.
    
    This handles various formats:
    - "Sol Ring" → ("Sol Ring", 1)
    - "1 Sol Ring" → ("Sol Ring", 1)
    - "10 Forest" → ("Forest", 10)
    - "3x Cultivate" → ("Cultivate", 3)
    - "# Comment" → ignored
    - "# Commander: Atraxa, Praetors' Voice" → sets commander
    
    Args:
        lines: List of lines from decklist file
    
    Returns:
        Tuple of (cards list, commander name or None)
    """
    cards = []
    commander = None
    
    for line in lines:
        line = line.strip()
        
        # Check for commander specification
        if line.startswith("# Commander:"):
            commander = line.replace("# Commander:", "").strip()
            continue
        
        # Skip empty lines and other comments
        if not line or line.startswith('#'):
            continue
        
        # Extract quantity (default 1)
        quantity = 1
        match = re.match(r'^(\d+)x?\s+(.+)$', line)
        
        if match:
            quantity = int(match.group(1))
            card_name = match.group(2)
        else:
            card_name = line
        
        # Clean card name (remove set codes, etc.)
        card_name = re.sub(r'\s*\([^)]+\)\s*$', '', card_name).strip()
        
        if card_name:
            cards.append((card_name, quantity))
    
    return cards, commander


async def fetch_deck_from_decklist(
    lines: list[str],
    commander_override: Optional[str] = None
) -> tuple[list[Card], Optional[str]]:
    """
    Fetch cards from a decklist and expand to full deck with duplicates.
    
    This is the main entry point for building a complete deck:
    1. Parse decklist to extract (card_name, quantity) pairs and commander
    2. Fetch unique cards from Scryfall (efficient: only 1 request per unique card)
    3. Expand to full deck by duplicating cards according to quantities
    
    Example:
        Input: ["# Commander: Atraxa", "1 Sol Ring", "10 Forest", "1 Command Tower"]
        - Fetches 3 unique cards from Scryfall
        - Returns (list of 12 Card instances, "Atraxa")
    
    Args:
        lines: Lines from decklist file
        commander_override: Optional commander name to override decklist
    
    Returns:
        Tuple of (full deck with duplicates, commander name or None)
    """
    # Parse decklist to get (name, quantity) pairs and commander
    card_quantities, commander_from_file = parse_decklist(lines)
    
    # Commander priority: override > file > None
    commander = commander_override or commander_from_file
    
    if not card_quantities:
        return [], commander
    
    # Get unique card names for Scryfall fetching (including commander if specified)
    unique_names = list(set(name for name, _ in card_quantities))
    if commander and commander not in unique_names:
        unique_names.append(commander)
    
    print(f"📝 Found {len(card_quantities)} entries, {len(unique_names)} unique cards")
    if commander:
        print(f"👑 Commander: {commander}")
    print(f"💾 Total cards in deck: {sum(qty for _, qty in card_quantities)}")
    
    # Fetch unique cards from Scryfall
    fetched_cards = await fetch_cards(unique_names)
    
    # Create lookup dictionary for fetched cards
    card_lookup = {card.name.lower(): card for card in fetched_cards}
    
    # Expand to full deck with duplicates, ensuring unique instances
    full_deck: list[Card] = []
    missing_cards = []
    import dataclasses # Not needed for Pydantic
    
    for card_name, quantity in card_quantities:
        # Normalize card_name for lookup, as Scryfall might return slightly different casing
        normalized_card_name = card_name.lower()
        
        if normalized_card_name in card_lookup:
            card_obj = card_lookup[normalized_card_name]
            for _ in range(quantity):
                # CRITICAL: Create a NEW instance for each card to avoid shared state
                # Since Card is a Pydantic Model (v2), use model_copy(deep=True)
                new_instance = card_obj.model_copy(deep=True)
                
                full_deck.append(new_instance)
        else:
            missing_cards.append(f"{quantity}x {card_name}")
    
    if missing_cards:
        print(f"\n⚠️  Missing cards (not found on Scryfall):")
        for missing in missing_cards:
            print(f"   - {missing}")
            
    if len(full_deck) < 100:
         print(f"⚠️  Note: Deck has {len(full_deck)} cards (Commander size usually 100). Check input list.")
    
    return full_deck, commander
