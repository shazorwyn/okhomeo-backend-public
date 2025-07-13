from rest_framework import serializers
from .models import *


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image"]


class DiseaseSerializer(serializers.ModelSerializer):
    category = CategorySerializer()

    class Meta:
        model = Disease
        fields = ["id", "name", "slug", "description", "category", "image"]


class CreateDiseaseSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field="id"
    )

    class Meta:
        model = Disease
        fields = ["name", "description", "image"]


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            "id",
            "name",
            "slug",
            "qualifications",
            "specialization",
            "description",
            "image",
        ]


class TreatmentSerializer(serializers.ModelSerializer):
    disease = DiseaseSerializer()

    class Meta:
        model = Treatment
        fields = ["id", "name", "slug", "disease", "description", "image"]


class CreateTreatmentSerializer(serializers.ModelSerializer):
    # disease = serializers.SlugRelatedField(
    #     queryset=Disease.objects.all(), slug_field="id"
    # )

    # def validate_disease_id(self, value):
    #     disease = Disease.objects.get(pk=value)
    #     if not disease:
    #         raise serializers.ValidationError(
    #             "Disease with the given id does not exists"
    #         )
    #     return value

    class Meta:
        model = Treatment
        fields = ["name", "description", "image"]


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "composition",
            "usage",
            "is_prescription_required",
            "manufacturer",
            "brand",
            "expiry_date",
            "manufacturing_date",
            "dosage",
            "side_effects",
            "image",
        ]


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = [
            "id",
            "achievement_title",
            "achiever",
            "award",
            "awarder",
            "description",
            "image",
        ]
