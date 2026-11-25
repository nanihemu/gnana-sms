"""Seed the five demo users, one per role.

Usage:
    python manage.py seed_demo_users
    python manage.py seed_demo_users --reset     # reset passwords too

Created once; re-running is idempotent (it updates first name/last name,
and resets the password when --reset is passed).
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo1234")

DEMO_USERS = [
    {
        "email": "superadmin@demo.gnana.in",
        "first_name": "Platform",
        "last_name": "Super",
        "role": "super_admin",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "admin@demo.gnana.in",
        "first_name": "School",
        "last_name": "Admin",
        "role": "admin",
    },
    {
        "email": "teacher@demo.gnana.in",
        "first_name": "Demo",
        "last_name": "Teacher",
        "role": "teacher",
    },
    {
        "email": "student@demo.gnana.in",
        "first_name": "Demo",
        "last_name": "Student",
        "role": "student",
    },
    {
        "email": "parent@demo.gnana.in",
        "first_name": "Demo",
        "last_name": "Parent",
        "role": "parent",
    },
]


class Command(BaseCommand):
    help = "Create/update the 5 demo users (one per role)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset the demo users to a known password on every run.",
        )

    def handle(self, *args, **options):
        reset = options["reset"]
        created, updated = [], []

        for spec in DEMO_USERS:
            email = spec["email"]
            user, was_created = User.objects.get_or_create(
                email=email,
                defaults={**spec, "password": ""},
            )
            if was_created:
                user.set_password(DEMO_PASSWORD)
                created.append(email)
            else:
                if reset:
                    user.set_password(DEMO_PASSWORD)
                for field, value in spec.items():
                    setattr(user, field, value)
            user.save()

            role_label = user.get_role_display()
            if not was_created:
                updated.append(f"{email} ({role_label})")

        self.stdout.write(self.style.SUCCESS(f"Created {len(created)} demo users:"))
        for email in created:
            self.stdout.write(f"  - {email} / {DEMO_PASSWORD}")
        self.stdout.write("Updated: " + (", ".join(updated) or "none"))
        self.stdout.write(self.style.WARNING("Demo password: " + DEMO_PASSWORD))
