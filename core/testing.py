from django.core.cache import cache
from django.test import TestCase


class BaseTestCase(TestCase):
    """Django rolls the database back between tests but leaves the cache alone.
    Singletons and throttle counters live in the cache, so clear it every test.
    """

    def setUp(self):
        super().setUp()
        cache.clear()
