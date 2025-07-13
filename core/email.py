from djoser import email
from djoser.conf import settings


class PasswordResetEmail(email.PasswordResetEmail):
    template_name = "core/email/password_reset.html"

    def get_context_data(self):
        context = super().get_context_data()
        djoser_settings = getattr(settings, "DJOSER", {})
        context["domain"] = djoser_settings.get("DOMAIN", "ok-homeo.vercel.app")
        context["site_name"] = djoser_settings.get("SITE_NAME", "OkHomeo")
        context["user_full_name"] = context["user"].get_full_name()
        print(context["user_full_name"])
        return context


class PasswordChangedConfirmationEmail(email.PasswordChangedConfirmationEmail):
    template_name = "core/email/password_changed_confirmation.html"
