from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Accounts app. `label` is what AUTH_USER_MODEL references."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "Accounts"
