from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User as BaseUser
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("mobile_number", "email", "first_name", "last_name", "is_staff")
    list_editable = ["first_name", "last_name"]
    ordering = ("mobile_number",)
    search_fields = ("mobile_number", "email", "first_name", "last_name")
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "mobile_number",
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                ),
            },
        ),
    )
