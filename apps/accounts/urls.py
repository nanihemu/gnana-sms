"""accounts URL table, one dashboard URL per role."""

from django.urls import path

from . import views
from .models import User

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path(
        "platform/dashboard/",
        views.RoleDashboardView.as_view(role=User.Role.SUPER_ADMIN),
        name=User.Role.SUPER_ADMIN + "_dashboard",
    ),
    path(
        "admin/dashboard/",
        views.RoleDashboardView.as_view(role=User.Role.ADMIN),
        name="admin_dashboard",
    ),
    path(
        "teacher/dashboard/",
        views.RoleDashboardView.as_view(role=User.Role.TEACHER),
        name="teacher_dashboard",
    ),
    path(
        "student/dashboard/",
        views.RoleDashboardView.as_view(role=User.Role.STUDENT),
        name="student_dashboard",
    ),
    path(
        "parent/dashboard/",
        views.RoleDashboardView.as_view(role=User.Role.PARENT),
        name="parent_dashboard",
    ),
]
