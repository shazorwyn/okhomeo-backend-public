from rest_framework import serializers
from djoser.serializers import (
    UserCreatePasswordRetypeSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer,
)
from djoser.serializers import UserSerializer as BaseUserSerializer
from feedback.models import Review
from feedback.serializers import CreateReviewSerializer, ReviewSerializer


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        fields = [
            "id",
            "username",
            "mobile_number",
            "email",
            "gender",
            "birth_date",
            "first_name",
            "last_name",
            "password",
        ]


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = [
            "id",
            "username",
            "mobile_number",
            "email",
            "first_name",
            "last_name",
            "gender",
            "birth_date",
            "is_staff",
        ]
        read_only_fields = ("username", "email", "mobile_number", "is_staff")


class DisplayUserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ["username", "first_name", "last_name"]


class ProductReviewSerializer(ReviewSerializer):
    user = DisplayUserSerializer(read_only=True)


class CreateProductReviewSerializer(CreateReviewSerializer):
    def save(self, **kwargs):
        review = super().save(**kwargs)
        if not review:
            review = Review.objects.create(
                user=self.context["request"].user,
                content_type=self.context["content_type"],
                object_id=self.context["object_id"],
                **self.validated_data,
            )
            review.content_type = self.context["content_type"].id
            review.object_id = self.context["object_id"]
        review.save()
        return review


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    message = serializers.CharField()
