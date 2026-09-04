import logging

from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache.backends.redis import RedisCache
from redis.exceptions import RedisError

logger = logging.getLogger("core.cache")


class ResilientRedisCache(RedisCache):
    """A Redis outage should make the site slower, not take it offline.

    Every operation degrades to a cache miss / no-op instead of raising, so
    `SingletonModel.load()` falls back to PostgreSQL, `cached_db` sessions fall
    back to the database, and DRF throttling fails open rather than 500-ing.
    """

    def _degrade(self, operation, exc):
        logger.warning("Redis unavailable, degrading cache %s: %s", operation, exc)

    def get(self, key, default=None, version=None):
        try:
            return super().get(key, default, version)
        except RedisError as exc:
            self._degrade("get", exc)
            return default

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        try:
            return super().set(key, value, timeout, version)
        except RedisError as exc:
            self._degrade("set", exc)

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        try:
            return super().add(key, value, timeout, version)
        except RedisError as exc:
            self._degrade("add", exc)
            return False

    def delete(self, key, version=None):
        try:
            return super().delete(key, version)
        except RedisError as exc:
            self._degrade("delete", exc)
            return False

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        try:
            return super().touch(key, timeout, version)
        except RedisError as exc:
            self._degrade("touch", exc)
            return False

    def has_key(self, key, version=None):
        try:
            return super().has_key(key, version)
        except RedisError as exc:
            self._degrade("has_key", exc)
            return False

    def get_many(self, keys, version=None):
        try:
            return super().get_many(keys, version)
        except RedisError as exc:
            self._degrade("get_many", exc)
            return {}

    def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        try:
            return super().set_many(data, timeout, version)
        except RedisError as exc:
            self._degrade("set_many", exc)
            return list(data)

    def delete_many(self, keys, version=None):
        try:
            return super().delete_many(keys, version)
        except RedisError as exc:
            self._degrade("delete_many", exc)

    def clear(self):
        try:
            return super().clear()
        except RedisError as exc:
            self._degrade("clear", exc)
