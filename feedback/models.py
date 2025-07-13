from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.conf import settings


class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    review = models.TextField(blank=True, null=True)
    rating = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    content_type = models.ForeignKey(to=ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_obj = GenericForeignKey("content_type", "object_id")

    _cached_allowed_content_types = None

    class Meta:
        unique_together = [["user", "content_type", "object_id"]]
        ordering = ["rating", "-created_at"]

    @classmethod
    def get_allowed_content_types(cls):
        if cls._cached_allowed_content_types is not None:
            return cls._cached_allowed_content_types
        allowed_types = []
        for ct_label in settings.FEEDBACK_APP.get("ALLOWED_REVIEW_ITEM_MODELS", []):
            if isinstance(ct_label, str):
                try:
                    app_label, model_name = ct_label.split(".")
                    ct = ContentType.objects.get(app_label=app_label, model=model_name)
                    allowed_types.append(ct)
                except ContentType.DoesNotExist:
                    raise ValueError(
                        f"Invalid content type: {ct_label}. Check ALLOWED_MODELS in settings."
                    )
            elif isinstance(ct_label, ContentType):
                allowed_types.append(ct_label)
            else:
                raise ValueError(f"Invalid type in ALLOWED_MODELS: {type(ct_label)}")
        cls._cached_allowed_content_types = allowed_types
        return allowed_types

    def clean(self):
        allowed_cts = self.get_allowed_content_types()
        if self.content_type not in allowed_cts:
            raise ValidationError(
                f"Invalid content type: {self.content_type} not in allowed types."
            )
        if (
            not self.content_type.model_class()
            .objects.filter(id=self.object_id)
            .exists()
        ):
            raise ValidationError(
                f"Linked object with id {self.object_id} does not exist."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
