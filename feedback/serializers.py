from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from . import models


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Review
        fields = [
            "id",
            "user",
            "rating",
            "review",
            "created_at",
            "updated_at",
        ]


class CreateReviewSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if not (1 <= data.get("rating", 0) <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")

        return data

    def save(self, **kwargs):
        if self.context.get("content_type") and self.context.get("object_id"):
            review = models.Review.objects.create(
                user=self.context["request"].user,
                content_type=self.context["content_type"],
                object_id=self.context["object_id"],
                **self.validated_data
            )
            return review
        return None

    class Meta:
        model = models.Review
        fields = ["id", "rating", "review", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class UpdateReviewSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if "rating" in data and not (1 <= data["rating"] <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return data

    class Meta:
        model = models.Review
        fields = ["id", "rating", "review", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
