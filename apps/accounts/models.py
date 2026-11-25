"""Custom User model: login by email, carries a role field.

The five roles are the fixed set from the product spec:
Super Admin (platform), Admin (per school), Teacher, Student, Parent.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserRoles(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    ADMIN = "admin", "School Admin"
    TEACHER = "teacher", "Teacher"
    STUDENT = "student", "Student"
    PARENT = "parent", "Parent"


class UserManager(BaseUserManager):
    """Manager for a User that has no username field.

    create_user / create_superuser take email directly instead of username.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRoles.SUPER_ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Gnana user. Identified by email; role picks which dashboard they land on."""

    username = None  # we log in with email instead
    email = models.EmailField("email address", unique=True)

    role = models.CharField(
        max_length=20,
        choices=UserRoles.choices,
        default=UserRoles.STUDENT,
        help_text="Platform role; decides the user's dashboard and permissions.",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # Sugar: User.Role is the same enum as UserRoles, for readable call sites.
    Role = UserRoles

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
