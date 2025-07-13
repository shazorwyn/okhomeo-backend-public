from django.contrib import admin
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html

from .models import Review


class ReviewAdminForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ALLOWED_MODELS = settings.FEEDBACK_APP.get("ALLOWED_REVIEW_ITEM_MODELS", [])
        ALLOWED_CONTENT_TYPES = []
        for ct_label in ALLOWED_MODELS:
            if isinstance(ct_label, str):
                try:
                    app_label, model_name = ct_label.split(".")
                    ALLOWED_CONTENT_TYPES.append(
                        ContentType.objects.get(app_label=app_label, model=model_name)
                    )
                except ContentType.DoesNotExist:
                    raise ValueError(
                        f"Invalid content type: {ct_label}. Check ALLOWED_CONTENT_TYPES in settings."
                    )
            elif isinstance(ct_label, ContentType):
                ALLOWED_CONTENT_TYPES.append(ct_label)
            else:
                raise ValueError(
                    f"ALLOWED_CONTENT_TYPES must contain strings or ContentType objects. Found: {type(ct_label)}"
                )

        CONTENT_TYPE_CHOICES = [
            (ct.id, ct.model_class()._meta.verbose_name.title())
            for ct in ALLOWED_CONTENT_TYPES
        ]

        self.fields["content_type"].queryset = ContentType.objects.filter(
            id__in=[ct.id for ct in ALLOWED_CONTENT_TYPES]
        )
        self.fields["content_type"].choices = CONTENT_TYPE_CHOICES


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm

    list_display = ["user", "item_type", "linked_object", "rating"]

    def item_type(self, review):
        return str(review.content_type)

    item_type.short_description = "Item Type"
    item_type.admin_order_field = "content_type"

    def linked_object(self, review):
        if review.content_type and review.object_id:
            model = review.content_type.model_class()
            try:
                obj = model.objects.get(pk=review.object_id)
            except model.DoesNotExist:
                return "Deleted"
            url = reverse(
                f"admin:{review.content_type.app_label}_{review.content_type.model}_change",
                args=[obj.pk],
            )
            return format_html('<a href="{}">{}</a>', url, str(obj))
        return "None"

    linked_object.short_description = "Object"
    linked_object.admin_order_field = "object_id"
