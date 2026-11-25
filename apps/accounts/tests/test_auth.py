"""Tests for auth: login page, role-based redirect, per-role dashboards,
access control, and the demo-user seed command."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse

from apps.accounts.models import UserRoles

User = get_user_model()

PASSWORD = "test-password-123"

# role -> (dashboard view name, expected title text)
ROLE_EXPECTATIONS = [
    (UserRoles.SUPER_ADMIN, "super_admin_dashboard", "Super Admin Dashboard"),
    (UserRoles.ADMIN, "admin_dashboard", "School Admin Dashboard"),
    (UserRoles.TEACHER, "teacher_dashboard", "Teacher Dashboard"),
    (UserRoles.STUDENT, "student_dashboard", "Student Dashboard"),
    (UserRoles.PARENT, "parent_dashboard", "Parent Dashboard"),
]


def make_user(role, email=None):
    """Create a user of the given role and return it."""
    return User.objects.create_user(
        email=email or f"{role}@example.com",
        password=PASSWORD,
        role=role,
    )


@pytest.mark.django_db
class TestLogin:
    def test_login_page_renders(self, client):
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 200
        assert b"Gnana" in response.content

    @pytest.mark.parametrize("role,dashboard_name,title", ROLE_EXPECTATIONS)
    def test_login_redirects_to_role_dashboard(
        self, client, role, dashboard_name, title
    ):
        make_user(role)
        dashboard_url = reverse(f"accounts:{dashboard_name}")

        response = client.post(
            reverse("accounts:login"),
            {"username": f"{role}@example.com", "password": PASSWORD},
        )

        assert response.status_code == 302
        assert response.headers["Location"] == dashboard_url

        # Follow the redirect and confirm the page is the right role dashboard.
        page = client.get(dashboard_url)
        assert page.status_code == 200
        assert title.encode() in page.content


@pytest.mark.django_db
class TestRoleDashboards:
    def test_dashboard_requires_login(self, client):
        response = client.get(reverse("accounts:teacher_dashboard"))
        assert response.status_code == 302
        assert reverse("accounts:login") in response.headers["Location"]

    def test_wrong_role_is_forbidden(self, client):
        make_user(UserRoles.STUDENT)
        client.login(username="student@example.com", password=PASSWORD)

        response = client.get(reverse("accounts:teacher_dashboard"))
        assert response.status_code == 403

    def test_each_role_sees_its_own_title(self, client):
        """The 5 demo dashboards differ per role."""
        titles = set()
        for role, dashboard_name, title in ROLE_EXPECTATIONS:
            make_user(role)
            client.login(username=f"{role}@example.com", password=PASSWORD)
            page = client.get(reverse(f"accounts:{dashboard_name}"))
            titles.add(title)
            assert title.encode() in page.content
        assert len(titles) == 5


@pytest.mark.django_db
class TestSeedCommand:
    def test_seed_creates_five_demo_users(self):
        call_command("seed_demo_users")

        assert User.objects.count() == 5
        roles = set(User.objects.values_list("role", flat=True))
        assert roles == {role for role, _, _ in ROLE_EXPECTATIONS}

        superadmin = User.objects.get(email="superadmin@demo.gnana.in")
        assert superadmin.is_staff and superadmin.is_superuser

    def test_seed_is_idempotent(self):
        call_command("seed_demo_users")
        call_command("seed_demo_users")
        assert User.objects.count() == 5
