"""Smoke tests for the generated project."""

from django.conf import settings
from django.test import SimpleTestCase


class SmokeTests(SimpleTestCase):
    def test_settings_are_configured(self):
        self.assertTrue(settings.SECRET_KEY)
        self.assertIn("django.contrib.admin", settings.INSTALLED_APPS)

    def test_database_backend_is_set(self):
        engine = settings.DATABASES["default"]["ENGINE"]
        self.assertTrue(engine.startswith("django.db.backends."))
