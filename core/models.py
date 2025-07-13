from django.db import models
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError


def mobile_number_validator(value):
    if not value.isdigit():
        raise ValidationError("Mobile number must contain numeric values only.")
    if len(value) != 10:
        raise ValidationError("Mobile number must contain 10 digits")


class User(AbstractUser):
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(
        unique=True,
        max_length=10,
        validators=[mobile_number_validator],
        verbose_name="Mobile Number",
        help_text="Enter a 10 digit Mobile Number",
    )
    MALE = "M"
    FEMALE = "F"
    CUSTOM = "C"
    GENDER_CHOICES = [(MALE, "Male"), (FEMALE, "Female"), (CUSTOM, "Custom")]
    gender = models.CharField(
        max_length=1, blank=True, null=True, choices=GENDER_CHOICES
    )
    birth_date = models.DateField(blank=True, null=True)

    REQUIRED_FIELDS = ["email", "mobile_number"]
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"

    USER_CREATE_PASSWORD_RETYPE = True

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return self.get_full_name()
