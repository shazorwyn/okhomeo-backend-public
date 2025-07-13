from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from . import models


class ProductAdminForm(forms.ModelForm):

    class Meta:
        model = models.Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ALLOWED_MODELS = settings.STORE_APP.get("ALLOWED_PRODUCT_MODELS", [])
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


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm

    list_display = [
        "name",
        "unit_price",
        "discount",
        "net_price",
        "stock",
        "product_type",
        "linked_object",
        "trending",
    ]

    def product_type(self, product):
        return str(product.content_type)

    product_type.short_description = "Product Type"
    product_type.admin_order_field = "content_type"

    def linked_object(self, product):
        if product.content_type and product.object_id:
            model = product.content_type.model_class()
            try:
                obj = model.objects.get(pk=product.object_id)
            except model.DoesNotExist:
                return "Deleted"
            url = reverse(
                f"admin:{product.content_type.app_label}_{product.content_type.model}_change",
                args=[obj.pk],
            )
            return format_html('<a href="{}">{}</a>', url, str(obj))
        return "None"

    linked_object.short_description = "Object"
    linked_object.admin_order_field = "object_id"


class CartItemInline(admin.StackedInline):
    model = models.CartItem
    extra = 0


@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["id"]
    inlines = [CartItemInline]


class OrderItemInline(admin.StackedInline):
    model = models.OrderItem
    extra = 0


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "payment_status",
        "order_status",
        "placed_at",
        "delivered_at",
        "cancelled_at",
    ]
    inlines = [OrderItemInline]
