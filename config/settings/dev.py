"""Dev settings — fast feedback, DEBUG on, no external hardening."""

from .base import *  # noqa: F403  (base.py holds everything; env decides the rest)

# DEBUG is already on via DJANGO_DEBUG in .env; fail loudly if unset.
assert DEBUG is True  # noqa: F405
