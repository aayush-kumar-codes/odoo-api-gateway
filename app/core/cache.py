from typing import Any, Optional
import json
import redis
from app.core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

def set_cache(key: str, value: Any, expire: int = 3600) -> bool:
    """
    Set a cache value with expiration time (default 1 hour)
    """
    try:
        redis_client.setex(key, expire, json.dumps(value))
        return True
    except Exception:
        return False

def get_cache(key: str) -> Optional[Any]:
    """
    Get a cached value
    """
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None

def delete_cache(key: str) -> bool:
    """
    Delete a cached value
    """
    try:
        redis_client.delete(key)
        return True
    except Exception:
        return False

def clear_cache_pattern(pattern: str) -> bool:
    """
    Clear all cache keys matching a pattern
    """
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
        return True
    except Exception:
        return False 