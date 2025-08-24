"""
Caching-lager för upprepade requests
"""

import asyncio
import hashlib
import json
import os
import pickle
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import structlog

from ..utils.config import Config


class CacheStrategy(Enum):
    """Cache-strategier"""

    MEMORY = "memory"
    DISK = "disk"
    REDIS = "redis"
    HYBRID = "hybrid"


@dataclass
class CacheEntry:
    """En cache-post"""

    key: str
    data: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: float = 0.0
    size: int = 0

    def is_expired(self) -> bool:
        """Kontrollerar om posten har gått ut"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def is_stale(self, max_age: float) -> bool:
        """Kontrollerar om posten är för gammal"""
        return time.time() - self.created_at > max_age

    def touch(self):
        """Uppdaterar access-information"""
        self.access_count += 1
        self.last_accessed = time.time()


class BaseCache:
    """Basklass för cache-implementationer"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = structlog.get_logger(f"{__name__}.{self.__class__.__name__}")

    async def get(self, key: str) -> Optional[Any]:
        """Hämtar data från cache"""
        raise NotImplementedError

    async def set(self, key: str, data: Any, ttl: Optional[float] = None) -> bool:
        """Sparar data i cache"""
        raise NotImplementedError

    async def delete(self, key: str) -> bool:
        """Tar bort data från cache"""
        raise NotImplementedError

    async def clear(self) -> bool:
        """Rensar hela cache"""
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        """Kontrollerar om nyckel finns"""
        raise NotImplementedError

    def get_stats(self) -> Dict[str, Any]:
        """Returnerar cache-statistik"""
        raise NotImplementedError


class MemoryCache(BaseCache):
    """Minne-baserad cache"""

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)

        # Cache-lagring
        self.cache: Dict[str, CacheEntry] = {}

        # Konfiguration
        self.max_size = self.config.get("cache.memory.max_size", 1000)
        self.default_ttl = self.config.get("cache.memory.default_ttl", 3600)  # 1 timme
        self.max_memory_mb = self.config.get("cache.memory.max_memory_mb", 100)

        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def start(self):
        """Startar cache med cleanup"""
        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Memory cache started")

    async def stop(self):
        """Stoppar cache"""
        self.is_running = False

        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Memory cache stopped")

    async def get(self, key: str) -> Optional[Any]:
        """Hämtar data från cache"""
        if key not in self.cache:
            return None

        entry = self.cache[key]

        # Kontrollera om posten har gått ut
        if entry.is_expired():
            del self.cache[key]
            return None

        # Uppdatera access-information
        entry.touch()

        return entry.data

    async def set(self, key: str, data: Any, ttl: Optional[float] = None) -> bool:
        """Sparar data i cache"""
        try:
            # Beräkna storlek
            size = self._calculate_size(data)

            # Kontrollera om vi behöver rensa cache
            if len(self.cache) >= self.max_size:
                await self._evict_entries()

            # Skapa cache-post
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            elif self.default_ttl is not None:
                expires_at = time.time() + self.default_ttl

            entry = CacheEntry(key=key, data=data, created_at=time.time(), expires_at=expires_at, size=size)

            self.cache[key] = entry
            return True

        except Exception as e:
            self.logger.error(f"Error setting cache entry {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Tar bort data från cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    async def clear(self) -> bool:
        """Rensar hela cache"""
        self.cache.clear()
        return True

    async def exists(self, key: str) -> bool:
        """Kontrollerar om nyckel finns"""
        if key not in self.cache:
            return False

        entry = self.cache[key]
        if entry.is_expired():
            del self.cache[key]
            return False

        return True

    def _calculate_size(self, data: Any) -> int:
        """Beräknar ungefärlig storlek på data"""
        try:
            return len(pickle.dumps(data))
        except:
            return 0

    async def _evict_entries(self):
        """Tar bort gamla poster för att göra plats"""
        if len(self.cache) < self.max_size:
            return

        # Sortera efter access-frekvens och ålder
        entries = list(self.cache.items())
        entries.sort(key=lambda x: (x[1].access_count, x[1].last_accessed))

        # Ta bort 10% av de minst använda
        to_remove = max(1, len(entries) // 10)

        for i in range(to_remove):
            key, _ = entries[i]
            del self.cache[key]

    async def _cleanup_loop(self):
        """Loop för att rensa utgångna poster"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Rensa varje minut
                await self._cleanup_expired()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {str(e)}")

    async def _cleanup_expired(self):
        """Rensar utgångna poster"""
        expired_keys = []

        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

    def get_stats(self) -> Dict[str, Any]:
        """Returnerar cache-statistik"""
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())

        total_size = sum(entry.size for entry in self.cache.values())
        avg_size = total_size / total_entries if total_entries > 0 else 0

        return {
            "type": "memory",
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "total_size_bytes": total_size,
            "avg_entry_size_bytes": avg_size,
            "max_size": self.max_size,
            "max_memory_mb": self.max_memory_mb,
        }


class DiskCache(BaseCache):
    """Disk-baserad cache"""

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config)

        # Cache-katalog
        self.cache_dir = self.config.get("cache.disk.directory", "cache")
        self.max_size_mb = self.config.get("cache.disk.max_size_mb", 1000)
        self.default_ttl = self.config.get("cache.disk.default_ttl", 86400)  # 24 timmar

        # Skapa cache-katalog
        os.makedirs(self.cache_dir, exist_ok=True)

        # Index-fil
        self.index_file = os.path.join(self.cache_dir, "index.json")
        self.index: Dict[str, Dict[str, Any]] = {}

        # Ladda index
        self._load_index()

    def _load_index(self):
        """Laddar cache-index"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, "r") as f:
                    self.index = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading cache index: {str(e)}")
            self.index = {}

    def _save_index(self):
        """Sparar cache-index"""
        try:
            with open(self.index_file, "w") as f:
                json.dump(self.index, f)
        except Exception as e:
            self.logger.error(f"Error saving cache index: {str(e)}")

    def _get_cache_path(self, key: str) -> str:
        """Hämtar cache-filsökväg"""
        # Skapa hash för säker filnamn
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")

    async def get(self, key: str) -> Optional[Any]:
        """Hämtar data från cache"""
        if key not in self.index:
            return None

        entry_info = self.index[key]
        cache_path = self._get_cache_path(key)

        # Kontrollera om filen finns
        if not os.path.exists(cache_path):
            del self.index[key]
            self._save_index()
            return None

        # Kontrollera om posten har gått ut
        if entry_info.get("expires_at") and time.time() > entry_info["expires_at"]:
            await self.delete(key)
            return None

        try:
            # Läs data från fil
            with open(cache_path, "rb") as f:
                data = pickle.load(f)

            # Uppdatera access-information
            entry_info["access_count"] += 1
            entry_info["last_accessed"] = time.time()
            self._save_index()

            return data

        except Exception as e:
            self.logger.error(f"Error reading cache file {cache_path}: {str(e)}")
            await self.delete(key)
            return None

    async def set(self, key: str, data: Any, ttl: Optional[float] = None) -> bool:
        """Sparar data i cache"""
        try:
            cache_path = self._get_cache_path(key)

            # Kontrollera disk-utrymme
            await self._check_disk_space()

            # Spara data till fil
            with open(cache_path, "wb") as f:
                pickle.dump(data, f)

            # Uppdatera index
            expires_at = None
            if ttl is not None:
                expires_at = time.time() + ttl
            elif self.default_ttl is not None:
                expires_at = time.time() + self.default_ttl

            file_size = os.path.getsize(cache_path)

            self.index[key] = {
                "file_path": cache_path,
                "created_at": time.time(),
                "expires_at": expires_at,
                "access_count": 0,
                "last_accessed": time.time(),
                "size": file_size,
            }

            self._save_index()
            return True

        except Exception as e:
            self.logger.error(f"Error setting cache entry {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Tar bort data från cache"""
        try:
            if key in self.index:
                cache_path = self._get_cache_path(key)

                # Ta bort fil
                if os.path.exists(cache_path):
                    os.remove(cache_path)

                # Ta bort från index
                del self.index[key]
                self._save_index()

                return True
            return False

        except Exception as e:
            self.logger.error(f"Error deleting cache entry {key}: {str(e)}")
            return False

    async def clear(self) -> bool:
        """Rensar hela cache"""
        try:
            # Ta bort alla cache-filer
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".cache"):
                    file_path = os.path.join(self.cache_dir, filename)
                    os.remove(file_path)

            # Rensa index
            self.index.clear()
            self._save_index()

            return True

        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Kontrollerar om nyckel finns"""
        if key not in self.index:
            return False

        entry_info = self.index[key]
        cache_path = self._get_cache_path(key)

        if not os.path.exists(cache_path):
            del self.index[key]
            self._save_index()
            return False

        if entry_info.get("expires_at") and time.time() > entry_info["expires_at"]:
            await self.delete(key)
            return False

        return True

    async def _check_disk_space(self):
        """Kontrollerar disk-utrymme och rensar vid behov"""
        total_size = sum(entry["size"] for entry in self.index.values())
        max_size_bytes = self.max_size_mb * 1024 * 1024

        if total_size > max_size_bytes:
            await self._evict_entries()

    async def _evict_entries(self):
        """Tar bort gamla poster för att frigöra disk-utrymme"""
        # Sortera efter access-frekvens och ålder
        entries = list(self.index.items())
        entries.sort(key=lambda x: (x[1]["access_count"], x[1]["last_accessed"]))

        # Ta bort 20% av de minst använda
        to_remove = max(1, len(entries) // 5)

        for i in range(to_remove):
            key, _ = entries[i]
            await self.delete(key)

    def get_stats(self) -> Dict[str, Any]:
        """Returnerar cache-statistik"""
        total_entries = len(self.index)
        expired_entries = sum(
            1 for entry in self.index.values() if entry.get("expires_at") and time.time() > entry["expires_at"]
        )

        total_size = sum(entry["size"] for entry in self.index.values())
        avg_size = total_size / total_entries if total_entries > 0 else 0

        return {
            "type": "disk",
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "total_size_bytes": total_size,
            "avg_entry_size_bytes": avg_size,
            "max_size_mb": self.max_size_mb,
            "cache_directory": self.cache_dir,
        }


class CacheManager:
    """
    Hanterar flera cache-lager
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = structlog.get_logger(__name__)

        # Cache-strategi
        self.strategy = CacheStrategy(self.config.get("cache.strategy", "memory"))

        # Cache-lager
        self.memory_cache: Optional[MemoryCache] = None
        self.disk_cache: Optional[DiskCache] = None
        self.redis_cache: Optional[Any] = None

        # Setup cache-lager
        self._setup_caches()

    def _setup_caches(self):
        """Sätter upp cache-lager enligt strategi"""
        if self.strategy in [CacheStrategy.MEMORY, CacheStrategy.HYBRID]:
            self.memory_cache = MemoryCache(self.config)

        if self.strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
            self.disk_cache = DiskCache(self.config)

        if self.strategy == CacheStrategy.REDIS:
            # Redis cache skulle implementeras här
            pass

    async def start(self):
        """Startar cache-manager"""
        if self.memory_cache:
            await self.memory_cache.start()

        self.logger.info(f"Cache manager started with strategy: {self.strategy.value}")

    async def stop(self):
        """Stoppar cache-manager"""
        if self.memory_cache:
            await self.memory_cache.stop()

        self.logger.info("Cache manager stopped")

    async def get(self, key: str) -> Optional[Any]:
        """Hämtar data från cache"""
        # Försök memory cache först
        if self.memory_cache:
            data = await self.memory_cache.get(key)
            if data is not None:
                return data

        # Försök disk cache
        if self.disk_cache:
            data = await self.disk_cache.get(key)
            if data is not None:
                # Populera memory cache
                if self.memory_cache:
                    await self.memory_cache.set(key, data)
                return data

        return None

    async def set(self, key: str, data: Any, ttl: Optional[float] = None) -> bool:
        """Sparar data i cache"""
        success = True

        # Spara i memory cache
        if self.memory_cache:
            success &= await self.memory_cache.set(key, data, ttl)

        # Spara i disk cache
        if self.disk_cache:
            success &= await self.disk_cache.set(key, data, ttl)

        return success

    async def delete(self, key: str) -> bool:
        """Tar bort data från cache"""
        success = True

        if self.memory_cache:
            success &= await self.memory_cache.delete(key)

        if self.disk_cache:
            success &= await self.disk_cache.delete(key)

        return success

    async def clear(self) -> bool:
        """Rensar alla cache-lager"""
        success = True

        if self.memory_cache:
            success &= await self.memory_cache.clear()

        if self.disk_cache:
            success &= await self.disk_cache.clear()

        return success

    async def exists(self, key: str) -> bool:
        """Kontrollerar om nyckel finns"""
        if self.memory_cache and await self.memory_cache.exists(key):
            return True

        if self.disk_cache and await self.disk_cache.exists(key):
            return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Returnerar statistik för alla cache-lager"""
        stats = {"strategy": self.strategy.value, "layers": {}}

        if self.memory_cache:
            stats["layers"]["memory"] = self.memory_cache.get_stats()

        if self.disk_cache:
            stats["layers"]["disk"] = self.disk_cache.get_stats()

        return stats

    def generate_cache_key(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Genererar cache-nyckel för URL och parametrar"""
        key_parts = [url]

        if params:
            # Sortera parametrar för konsistent nyckel
            sorted_params = sorted(params.items())
            key_parts.append(json.dumps(sorted_params, sort_keys=True))

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
