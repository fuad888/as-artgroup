import logging
import time

from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache.backends.redis import RedisCache
from redis.exceptions import RedisError

logger = logging.getLogger("core.cache")

# How long to stop talking to Redis after it fails. Long enough that an outage
# costs one failed connection rather than one per cache operation, short enough
# that the site picks Redis back up on its own.
COOLDOWN_SECONDS = 30


class ResilientRedisCache(RedisCache):
    """A Redis outage should make the site slower, not take it offline — and it
    must not make it *much* slower either.

    Every operation degrades to a cache miss / no-op instead of raising, so
    `SingletonModel.load()` falls back to the database, `cached_db` sessions
    fall back to the database, and DRF throttling fails open rather than 500-ing.

    Degrading alone is not enough. With socket_connect_timeout=3 and a page that
    touches the cache several times, an unreachable Redis turns every request
    into a multi-second wait — the site looks frozen even though nothing is
    broken. That is the common shape of this failure: REDIS_URL is set in .env
    but the host has no Redis. So after a failure the backend stops dialling for
    a cooldown and answers from the fallback immediately.
    """

    # On the class, so every thread in a worker shares one breaker.
    _unavailable_until = 0.0

    def _is_open(self):
        return time.monotonic() < type(self)._unavailable_until

    def _trip(self, operation, exc):
        already_open = self._is_open()
        type(self)._unavailable_until = time.monotonic() + COOLDOWN_SECONDS
        if already_open:
            logger.debug("Redis still unavailable (%s): %s", operation, exc)
        else:
            logger.warning(
                "Redis unavailable, serving from the fallback for %ss (%s): %s",
                COOLDOWN_SECONDS, operation, exc,
            )

    def _reset(self):
        if type(self)._unavailable_until:
            type(self)._unavailable_until = 0.0
            logger.info("Redis reachable again")

    def _call(self, operation, fallback, func, *args, **kwargs):
        """Run a Redis operation, or skip straight to the fallback while the
        breaker is open. `fallback` is a callable so it is only built if used."""
        if self._is_open():
            return fallback()
        try:
            result = func(*args, **kwargs)
        except RedisError as exc:
            self._trip(operation, exc)
            return fallback()
        self._reset()
        return result

    def get(self, key, default=None, version=None):
        return self._call("get", lambda: default, super().get, key, default, version)

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        return self._call(
            "set", lambda: None, super().set, key, value, timeout, version
        )

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        return self._call(
            "add", lambda: False, super().add, key, value, timeout, version
        )

    def delete(self, key, version=None):
        return self._call("delete", lambda: False, super().delete, key, version)

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        return self._call("touch", lambda: False, super().touch, key, timeout, version)

    def has_key(self, key, version=None):
        return self._call("has_key", lambda: False, super().has_key, key, version)

    def get_many(self, keys, version=None):
        return self._call("get_many", dict, super().get_many, keys, version)

    def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        return self._call(
            "set_many", lambda: list(data), super().set_many, data, timeout, version
        )

    def delete_many(self, keys, version=None):
        return self._call(
            "delete_many", lambda: None, super().delete_many, keys, version
        )

    def clear(self):
        return self._call("clear", lambda: None, super().clear)
