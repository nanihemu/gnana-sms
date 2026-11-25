"""Auth views: login that lands on the right role dashboard, and the
role dashboards themselves (one empty workspace per role).
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic.base import TemplateView

from .models import User

# role -> (URL path stem, URL name). Kept in one place so login redirect and
# the URL table can never drift apart.
ROLE_DASHBOARD = {
    User.Role.SUPER_ADMIN: ("platform", "accounts:super_admin_dashboard"),
    User.Role.ADMIN: ("admin", "accounts:admin_dashboard"),
    User.Role.TEACHER: ("teacher", "accounts:teacher_dashboard"),
    User.Role.STUDENT: ("student", "accounts:student_dashboard"),
    User.Role.PARENT: ("parent", "accounts:parent_dashboard"),
}


class LoginView(DjangoLoginView):
    """Django's LoginView, but the success URL depends on the user's role."""

    template_name = "accounts/login.html"

    def get_success_url(self):
        # Honour a safe ?next= from the login form, as LoginView normally does.
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url

        url_name = ROLE_DASHBOARD[self.request.user.role][1]
        return reverse(url_name)


class LogoutView(DjangoLogoutView):
    next_page = "accounts:login"


class RoleDashboardView(LoginRequiredMixin, TemplateView):
    """One empty dashboard per role.

    The URL already encodes the expected role (e.g. /teacher/dashboard/).
    We refuse to serve it to a user whose role does not match.
    """

    template_name = "accounts/role_dashboard.html"
    role = None  # set per URL pattern

    def dispatch(self, request, *args, **kwargs):
        # Anonymous users fall through to LoginRequiredMixin (redirect to login).
        if request.user.is_authenticated and request.user.role != self.role:
            return HttpResponseForbidden("You do not belong to this role's dashboard.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role"] = self.role
        context["role_label"] = User.Role(self.role).label
        context["dashboard_title"] = f"{User.Role(self.role).label} Dashboard"
        return context
