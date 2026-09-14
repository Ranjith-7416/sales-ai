"""Cache Service - Redis-based caching for expensive operations"""
from typing import Optional, Dict, Any
try:
    import redis
except ImportError:
    redis = None
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Redis caching service"""

    def __init__(self):
        self.redis_client = None
        self.in_memory_cache = {}
        if redis is not None:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=settings.REDIS_TIMEOUT_SECONDS,
                    socket_connect_timeout=settings.REDIS_TIMEOUT_SECONDS,
                )
                self.redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed: {str(e)}. Using in-memory cache.")
                self.redis_client = None

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                return self.in_memory_cache.get(key)
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {str(e)}")
        return None

    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600):
        """Set value in cache with TTL (default 1 hour)"""
        try:
            value_json = json.dumps(value)
            if self.redis_client:
                self.redis_client.setex(key, ttl, value_json)
            else:
                self.in_memory_cache[key] = value
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {str(e)}")

    async def delete(self, key: str):
        """Delete value from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self.in_memory_cache.pop(key, None)
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {str(e)}")

    async def clear_all(self):
        """Clear all cache"""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.in_memory_cache.clear()
        except Exception as e:
            logger.warning(f"Cache clear failed: {str(e)}")

    def cache_key_search(self, company_name: str) -> str:
        """Generate cache key for company search"""
        return f"search:company:{company_name.lower().replace(' ', '_')}"

    def cache_key_qualification(self, lead_id: str) -> str:
        """Generate cache key for lead qualification"""
        return f"qualification:{lead_id}"

    def cache_key_kb_search(self, query: str) -> str:
        """Generate cache key for KB search"""
        return f"kb_search:{query.lower().replace(' ', '_')}"


# Singleton instance
_cache_service = None


def get_cache_service() -> CacheService:
    """Get or create cache service singleton"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
