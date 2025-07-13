from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
from django.core.exceptions import ValidationError
from uuid import uuid4


class Product(models.Model):
    name = models.CharField(max_length=255, unique=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_digital = models.BooleanField(default=False)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    net_price = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=1)
    trending = models.BooleanField(default=False)
    preview_image = models.ImageField(upload_to="products/", blank=True, null=True)

    content_type = models.ForeignKey(to=ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_obj = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    track_stock = models.BooleanField(default=True)

    _cached_allowed_content_types = None

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id"], name="unique_product_per_object"
            )
        ]

    @classmethod
    def get_allowed_content_types(cls):
        if cls._cached_allowed_content_types is not None:
            return cls._cached_allowed_content_types

        allowed_types = []
        for ct_label in settings.STORE_APP.get("ALLOWED_PRODUCT_MODELS", []):
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
        if self.discount < 0 or self.discount > 100:
            raise ValidationError("Discount must be between 0 and 100")

    def save(self, *args, **kwargs):
        self.full_clean()
        self.net_price = self.get_net_price()
        self.update_from_content_obj()
        super().save(*args, **kwargs)

    def update_from_content_obj(self):
        if not self.content_obj:
            raise ValidationError("Content object must be set before saving.")

        self.name = str(self.content_obj)

        self.slug = slugify(self.name) or slugify(str(self.content_obj))

        for field in ["image", "thumbnail", "cover", "preview", "cover_image"]:
            candidate = getattr(self.content_obj, field, None)
            if callable(candidate):
                candidate = candidate()
            if candidate:
                self.preview_image = candidate
                break

    @property
    def is_available(self):
        return self.stock > 0

    @property
    def availability_status(self):
        return "In stock" if self.is_available else "Out of stock"

    def get_net_price(self):
        discount_multiplier = Decimal("1") - self.discount / Decimal("100")
        return (self.unit_price * discount_multiplier).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    def get_product_url(self):
        if hasattr(self.content_obj, "get_absolute_url"):
            return self.content_obj.get_absolute_url()
        return None

    def consume_stock(self, quantity=1):
        if self.track_stock:
            if self.stock < quantity:
                raise ValidationError(f"Not enough stock to consume for {self.name}")
            self.stock -= quantity
            self.save()

    def restore_stock(self, quantity=1):
        if self.track_stock:
            self.stock += quantity
            self.save()

    def __str__(self):
        return self.name or str(self.content_obj)


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart"
    )
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self):
        return sum(item.price for item in self.cart_items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        to=Cart, on_delete=models.CASCADE, related_name="cart_items"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def price(self):
        return self.product.get_net_price() * self.quantity

    class Meta:
        unique_together = [["cart", "product"]]


class ShippingDetail(models.Model):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=10)
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)

    def get_delivery_charge(self):
        return Decimal("60.00")

    def __str__(self):
        return f"{self.full_name} - {self.city} ({self.pincode}) ({self.state})"


class Order(models.Model):
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    PAYMENT_STATUS_PENDING = "P"
    PAYMENT_STATUS_SUCCESSFUL = "S"
    PAYMENT_STATUS_UNSUCCESSFUL = "U"
    PAYMENT_STATUS_REFUNDED = "R"
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, "Pending"),
        (PAYMENT_STATUS_SUCCESSFUL, "Successful"),
        (PAYMENT_STATUS_UNSUCCESSFUL, "Unsuccessful"),
        (PAYMENT_STATUS_REFUNDED, "Refunded"),
    ]
    PAYMENT_METHOD_RAZORPAY = "razorpay"
    PAYMENT_METHOD_COD = "cod"
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_METHOD_RAZORPAY, "Online Payment (Razorpay)"),
        (PAYMENT_METHOD_COD, "Cash on Delivery"),
    ]

    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default=PAYMENT_METHOD_RAZORPAY
    )
    payment_status = models.CharField(
        max_length=1, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_STATUS_PENDING
    )
    ORDER_STATUS_PROCESSING = "P"
    ORDER_STATUS_DISPATCHED = "D"
    ORDER_STATUS_SHIPPED = "S"
    ORDER_STATUS_OUT_FOR_DELIVERY = "O"
    ORDER_STATUS_COMPLETED = "C"
    ORDER_STATUS_CANCELLED = "X"
    ORDER_STATUS_CHOICES = [
        (ORDER_STATUS_PROCESSING, "Processing"),
        (ORDER_STATUS_DISPATCHED, "Dispatched"),
        (ORDER_STATUS_SHIPPED, "Shipped"),
        (ORDER_STATUS_OUT_FOR_DELIVERY, "Out for Delivery"),
        (ORDER_STATUS_COMPLETED, "Completed"),
        (ORDER_STATUS_CANCELLED, "Cancelled"),
    ]
    order_status = models.CharField(
        max_length=1, choices=ORDER_STATUS_CHOICES, default=ORDER_STATUS_PROCESSING
    )
    placed_at = models.DateTimeField(auto_now_add=True)
    refund_id = models.CharField(max_length=100, blank=True, null=True)
    REFUND_STATUS_NONE = "N"
    REFUND_STATUS_PENDING = "P"
    REFUND_STATUS_SUCCESSFUL = "S"
    REFUND_STATUS_FAILED = "F"
    REFUND_STATUS_CHOICES = [
        (REFUND_STATUS_NONE, "None"),
        (REFUND_STATUS_PENDING, "Pending"),
        (REFUND_STATUS_SUCCESSFUL, "Successful"),
        (REFUND_STATUS_FAILED, "Failed"),
    ]
    refunded_at = models.DateTimeField(blank=True, null=True)
    refund_status = models.CharField(
        max_length=1, choices=REFUND_STATUS_CHOICES, default=REFUND_STATUS_NONE
    )
    shipping_details = models.ForeignKey(
        to=ShippingDetail,
        on_delete=models.PROTECT,
        related_name="order",
        blank=True,
        null=True,
    )
    total_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    DELIVERY_METHOD_HOME = "home"
    DELIVERY_METHOD_PICKUP = "pickup"
    DELIVERY_METHOD_CHOICES = [
        (DELIVERY_METHOD_HOME, "Home Delivery"),
        (DELIVERY_METHOD_PICKUP, "Pickup from Store"),
    ]
    delivery_charge = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    delivery_method = models.CharField(
        max_length=10, choices=DELIVERY_METHOD_CHOICES, default=DELIVERY_METHOD_HOME
    )
    delivered_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    def get_delivery_charge(self, delivery_method="home"):
        if delivery_method == "home":
            return Decimal("60.00")
        elif delivery_method == "pickup":
            return Decimal("0.00")
        return Decimal("60.00")

    def get_total_price(self):
        return sum(item.price for item in self.order_items.all()) + self.delivery_charge

    def can_be_cancelled(self):
        return self.order_status == self.ORDER_STATUS_PROCESSING

    def mark_as_cancelled(self):
        self.order_status = self.ORDER_STATUS_CANCELLED
        self.cancelled_at = timezone.now()
        self.save()

    def cancel(self):
        if not self.can_be_cancelled():
            return ValidationError("Order can not be cancelled now.")
        self.mark_as_cancelled()

    def can_be_refunded(self):
        return (
            self.refund_status != self.REFUND_STATUS_SUCCESSFUL
            and self.payment_status == self.PAYMENT_STATUS_SUCCESSFUL
            and self.payment_method == self.PAYMENT_METHOD_RAZORPAY
        )

    def mark_as_refunded(self, refund_id):
        self.refund_id = refund_id
        self.refunded_at = timezone.now()
        self.refund_status = self.REFUND_STATUS_SUCCESSFUL
        self.payment_status = self.PAYMENT_STATUS_REFUNDED
        self.save()

    def mark_refund_failed(self):
        self.refund_status = self.REFUND_STATUS_FAILED
        self.save()

    def mark_payment_as_failed(self):
        self.payment_status = self.PAYMENT_STATUS_UNSUCCESSFUL
        self.save()

    def update_order_status(self, order_status):
        self.order_status = order_status
        self.save()

    def mark_as_completed(self):
        self.order_status = self.ORDER_STATUS_COMPLETED
        self.delivered_at = timezone.now()
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(
        to=Order, on_delete=models.CASCADE, related_name="order_items"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def price(self):
        return self.product.get_net_price() * self.quantity

    class Meta:
        unique_together = [["order", "product"]]
