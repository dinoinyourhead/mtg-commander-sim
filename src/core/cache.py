"""Scryfall API cache for reducing API calls."""

import json
import time
from pathlib import Path
from typing import Optional


class ScryfallCache:
    """
    File-based cache for Scryfall API responses.
    
    Caches card data locally to reduce API calls and improve performance.
    Each cached card has a TTL (time-to-live) of 24 hours.
    """
    
    def __init__(self, cache_dir: str = "data/scryfall_cache", ttl_hours: int = 24):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours (default: 24)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_hours * 3600
        
        # Load index
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> dict:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_index(self):
        """Save cache index to disk."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _get_cache_key(self, card_name: str) -> str:
        """Generate cache key from card name."""
        # Normalize: lowercase, replace special chars
        return card_name.lower().replace(" ", "_").replace(",", "").replace("'", "")
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        age = time.time() - timestamp
        return age > self.ttl_seconds
    
    def get(self, card_name: str) -> Optional[dict]:
        """
        Get card data from cache.
        
        Args:
            card_name: Name of the card
        
        Returns:
            Cached card data or None if not found/expired
        """
        key = self._get_cache_key(card_name)
        
        if key not in self.index:
            return None
        
        entry = self.index[key]
        
        # Check if expired
        if self._is_expired(entry["timestamp"]):
            # Remove expired entry
            del self.index[key]
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
            self._save_index()
            return None
        
        # Load from file
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def put(self, card_name: str, card_data: dict):
        """
        Store card data in cache.
        
        Args:
            card_name: Name of the card
            card_data: Scryfall card data
        """
        key = self._get_cache_key(card_name)
        
        # Save to file
        cache_file = self.cache_dir / f"{key}.json"
        with open(cache_file, 'w') as f:
            json.dump(card_data, f, indent=2)
        
        # Update index
        self.index[key] = {
            "card_name": card_name,
            "timestamp": time.time(),
            "file": f"{key}.json"
        }
        self._save_index()
    
    def clear_expired(self):
        """Remove all expired entries from cache."""
        expired_keys = []
        
        for key, entry in self.index.items():
            if self._is_expired(entry["timestamp"]):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.index[key]
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
        
        if expired_keys:
            self._save_index()
        
        return len(expired_keys)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total = len(self.index)
        expired = sum(1 for entry in self.index.values() if self._is_expired(entry["timestamp"]))
        valid = total - expired
        
        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": expired,
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.ttl_seconds / 3600,
        }
