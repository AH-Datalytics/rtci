import os
import time
from pathlib import Path

import BTrees.OOBTree
import ZODB
import ZODB.FileStorage
import persistent
import transaction

from rtci.util.log import logger


class CacheEntry(persistent.Persistent):
    """A persistent cache entry that stores a value with expiration information."""

    def __init__(self, value, ttl=None):
        """
        Initialize a new cache entry.

        Args:
            value: The value to store in the cache.
            ttl: Time to live in seconds. If None, the entry doesn't expire.
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl

    def is_expired(self):
        """Check if the cache entry is expired."""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)


class FileCache:
    """
    A file-based cache using ZODB for persistence with TTL support.
    """

    @classmethod
    def create(cls, cache_path: str | Path = os.environ.get("CACHE_PATH", "cache/zodb")):
        return FileCache(cache_path)

    def __init__(self, cache_path, default_ttl=None, cleanup_interval: int = None):
        """
        Initialize the cache.
        
        Args:
            cache_path: Path to the ZODB file storage.
            default_ttl: Default time to live in seconds for cache entries.
                         If 0, entries don't expire by default.
            cleanup_interval: Interval in seconds between automatic cleanup operations.
        """
        # default parameters
        if default_ttl is None:
            default_ttl = 30 * 60  # 30 minutes
        if cleanup_interval is None:
            cleanup_interval = 60 * 60  # 60 minutes

        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)

        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self.storage = ZODB.FileStorage.FileStorage(cache_path)
        self.db = ZODB.DB(self.storage)
        self.connection = self.db.open()
        self.root = self.connection.root()

        # Initialize cache container if it doesn't exist
        if 'cache' not in self.root:
            self.root['cache'] = BTrees.OOBTree.BTree()
            self.root['last_cleanup'] = time.time()
            transaction.commit()
        elif 'last_cleanup' not in self.root:
            self.root['last_cleanup'] = time.time()
            transaction.commit()

    def __del__(self):
        """Clean up resources when the object is garbage collected."""
        try:
            self.connection.close()
            self.db.close()
            self.storage.close()
        except:
            pass

    def set(self, key, value, ttl=None):
        """
        Store a value in the cache.
        
        Args:
            key: The key to store the value under.
            value: The value to store.
            ttl: Time to live in seconds. If None, uses the default_ttl.
                 If default_ttl is also None, the entry doesn't expire.
        """
        if ttl is None:
            ttl = self.default_ttl

        self.root['cache'][key] = CacheEntry(value, ttl)
        transaction.commit()

        self._check_cleanup()

    def get(self, key, default=None):
        """
        Retrieve a value from the cache.
        
        Args:
            key: The key to retrieve.
            default: The value to return if the key is not found or is expired.
        
        Returns:
            The cached value, or default if the key is not found or is expired.
        """
        entry = self.root['cache'].get(key)
        if entry is None:
            self._check_cleanup()
            return default

        if entry.is_expired():
            logger().info(f"Cache entry for key '{key}' is expired. Deleting it.")
            self.delete(key)
            return default

        self._check_cleanup()
        return entry.value

    def delete(self, key):
        """
        Remove a key from the cache.
        
        Args:
            key: The key to remove.
        
        Returns:
            True if the key was removed, False otherwise.
        """
        result = False
        if key in self.root['cache']:
            del self.root['cache'][key]
            transaction.commit()
            result = True

        self._check_cleanup()
        return result

    def clear(self):
        """Clear all entries from the cache."""
        self.root['cache'] = BTrees.OOBTree.BTree()
        self.root['last_cleanup'] = time.time()
        transaction.commit()

    def clear_expired(self):
        """Remove all expired entries from the cache."""
        keys_to_delete = []

        for key, entry in self.root['cache'].items():
            if entry.is_expired():
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.root['cache'][key]

        if keys_to_delete:
            transaction.commit()

        return len(keys_to_delete)

    def close(self):
        """Close the cache and free resources."""
        self.connection.close()
        self.db.close()
        self.storage.close()

    def _check_cleanup(self):
        """Check if it's time to clean up expired entries and do it if necessary."""
        if self.cleanup_interval is None or self.cleanup_interval <= 0:
            return
        current_time = time.time()
        if current_time - self.root['last_cleanup'] > self.cleanup_interval:
            self.clear_expired()
            self.root['last_cleanup'] = current_time
            transaction.commit()
