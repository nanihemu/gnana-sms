"""Test settings — fast in-memory SQLite, fast password hashing.

Tests must never depend on Docker / Postgres running, so we swap the
database engine here. RLS-specific behaviour (real Postgres) is tested
later under a Postgres-backed job in CI-like runs.
"""

from .base import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# MD5 hashing keeps password setup fast under pytest.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
