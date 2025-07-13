from django.contrib import admin
from .models import *


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


class CategoryInline(admin.TabularInline):
    model = Category


@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ["name", "category"]
    search_fields = ["name"]
    list_filter = ["category"]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ["name", "disease"]
    search_fields = ["name", "disease__name"]


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ["name", "is_prescription_required"]
    search_fields = ["name"]
    list_filter = ["is_prescription_required"]


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ["achievement_title", "achiever", "award", "awarder"]
    search_fields = ["achievement_title", "achiever"]
