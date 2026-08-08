"""Guards the auth rate-limiting added for production hardening.

Throttling is disabled process-wide during the test run (settings.py drops the
rates to None so accumulated auth calls don't trip unrelated tests). DRF binds
each throttle's rate table at import time, so `override_settings` can't reach an
already-imported throttle class -- the reliable way to exercise a throttle in a
test is to set its `rate` directly, which is what these tests do (3/min), with
the throttle cache cleared around each case.
"""

from unittest import mock

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import User
from .throttling import LoginRateThrottle


class LoginThrottleTests(APITestCase):
    def setUp(self):
        cache.clear()
        patcher = mock.patch.object(LoginRateThrottle, "rate", "3/min", create=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(cache.clear)

        self.client = APIClient()
        User.objects.create_user(username="throttle_target", email="t@example.com", password="Correct123!")

    def _attempt(self, username="throttle_target", password="wrong-password"):
        return self.client.post(
            "/api/auth/login/",
            {"username": username, "password": password},
            format="json",
        )

    def test_login_is_throttled_after_the_limit(self):
        # First 3 wrong-password attempts are allowed through (401); the 4th is
        # blocked by the rate limiter (429) -- credential stuffing is capped.
        for _ in range(3):
            self.assertEqual(self._attempt().status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self._attempt().status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_throttle_is_keyed_per_account_not_globally(self):
        # Exhaust the limit for throttle_target...
        for _ in range(4):
            self._attempt()
        self.assertEqual(self._attempt().status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # ...a different account is unaffected: the throttle keys on the submitted
        # identifier, so one account's attackers can't lock everyone else out.
        User.objects.create_user(username="other_account", email="o@example.com", password="Correct123!")
        self.assertEqual(
            self._attempt(username="other_account").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
