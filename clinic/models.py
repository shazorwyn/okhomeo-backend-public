from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify


class SlugifiedNameMixin(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(SlugifiedNameMixin):
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="category_images", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"


class Disease(SlugifiedNameMixin):
    category = models.ForeignKey(
        to=Category, related_name="diseases", on_delete=models.CASCADE
    )
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="disease_images", blank=True, null=True)


class Doctor(SlugifiedNameMixin):
    qualifications = models.CharField(max_length=255)
    specializations = models.ManyToManyField(to=Category)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="doctor_images", blank=True, null=True)


class Treatment(SlugifiedNameMixin):
    disease = models.ForeignKey(
        to=Disease,
        related_name="treatments",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="treatment_images", blank=True, null=True)

    def get_absolute_url(self):
        return reverse("treatment-detail", kwargs={"slug": self.slug})


class Medicine(SlugifiedNameMixin):
    description = models.TextField(blank=True, null=True)
    composition = models.TextField(blank=True, null=True)
    usage = models.TextField(blank=True, null=True)

    is_prescription_required = models.BooleanField(default=True)

    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    brand = models.CharField(max_length=255, blank=True, null=True)

    expiry_date = models.DateField(blank=True, null=True)
    manufacturing_date = models.DateField(blank=True, null=True)

    dosage = models.CharField(max_length=255, blank=True, null=True)
    side_effects = models.TextField(blank=True, null=True)

    image = models.ImageField(upload_to="medicine_images", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse("medicine-detail", kwargs={"slug": self.slug})


class Achievement(models.Model):
    achievement_title = models.CharField(max_length=255)
    achiever = models.CharField(max_length=255)
    award = models.CharField(max_length=255)
    awarder = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="achievement_images", blank=True, null=True)
