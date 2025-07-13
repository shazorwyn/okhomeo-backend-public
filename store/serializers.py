from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
import razorpay
from rest_framework import serializers
from . import models


class ProductSerializer(serializers.ModelSerializer):
    content_type = serializers.SlugRelatedField(
        queryset=ContentType.objects.all(), slug_field="model"
    )
    product_url = serializers.SerializerMethodField()

    def get_product_url(self, product):
        url = product.get_product_url()
        if not url:
            return None
        request = self.context.get("request")
        if request is None:
            return url
        return request.build_absolute_uri(url)

    class Meta:
        model = models.Product
        fields = [
            "id",
            "name",
            "slug",
            "unit_price",
            "is_available",
            "stock",
            "trending",
            "discount",
            "net_price",
            "preview_image",
            "content_type",
            "product_url",
            "track_stock",
        ]


class CreateProductSerializer(serializers.ModelSerializer):
    content_type = serializers.SlugRelatedField(
        queryset=ContentType.objects.all(), slug_field="model"
    )

    def validate(self, data):
        content_type = data.get("content_type")
        object_id = data.get("object_id")

        discount = data.get("discount", 0)
        if discount < 0 or discount > 100:
            raise serializers.ValidationError("Discount must be between 0 and 100.")

        # Check if the object exists for the content_type and object_id
        model_class = content_type.model_class()
        if not model_class.objects.filter(id=object_id).exists():
            raise serializers.ValidationError(
                f"Object with id {object_id} does not exist in {content_type}."
            )

        # Optional: Validate content_type is allowed (same as Product model)
        allowed_cts = models.Product.get_allowed_content_types()
        if content_type not in allowed_cts:
            raise serializers.ValidationError(
                f"Content type '{content_type}' is not allowed."
            )

        return data

    class Meta:
        model = models.Product
        fields = [
            "unit_price",
            "discount",
            "stock",
            "trending",
            "content_type",
            "object_id",
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = models.CartItem
        fields = ["id", "product", "quantity", "price"]


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        product = models.Product.objects.filter(pk=value).first()
        if not product:
            raise serializers.ValidationError("No Product with given id exists.")
        quantity = self.initial_data.get("quantity", 1)
        if product.stock < int(quantity):
            raise serializers.ValidationError(
                "Requested quantity exceeds available stock."
            )
        return value

    def save(self, **kwargs):
        cart_id = self.context["cart_id"]
        product_id = self.validated_data["product_id"]
        quantity = self.validated_data["quantity"]

        try:
            cart_item = models.CartItem.objects.get(
                cart_id=cart_id, product_id=product_id
            )
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except models.CartItem.DoesNotExist:
            self.instance = models.CartItem.objects.create(
                cart_id=cart_id, product_id=product_id, quantity=quantity
            )
        return self.instance

    class Meta:
        model = models.CartItem
        fields = ["id", "product_id", "quantity"]


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CartItem
        fields = ["quantity"]


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    cart_items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart):
        return sum([item.price for item in cart.cart_items.all()])

    class Meta:
        model = models.Cart
        fields = ["id", "user", "cart_items", "total_price"]


class CreateCartSerializer(serializers.Serializer):
    def save(self, **kwargs):
        models.Cart.objects.filter(user=self.context["user"]).delete()
        cart = models.Cart.objects.create(user=self.context["user"])
        return cart


class ShippingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ShippingDetail
        fields = [
            "id",
            "full_name",
            "phone",
            "address_line",
            "city",
            "state",
            "pincode",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = models.OrderItem
        fields = ["id", "product", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True)
    shipping_details = ShippingDetailSerializer()

    class Meta:
        model = models.Order
        fields = [
            "id",
            "order_items",
            "payment_status",
            "order_status",
            "refund_status",
            "total_price",
            "delivery_charge",
            "payment_method",
            "delivery_method",
            "placed_at",
            "delivered_at",
            "cancelled_at",
            "refunded_at",
            "shipping_details",
            "razorpay_order_id",
        ]


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Order
        fields = ["payment_status", "order_status"]


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()
    delivery_method = serializers.ChoiceField(
        choices=models.Order.DELIVERY_METHOD_CHOICES,
        default=models.Order.DELIVERY_METHOD_HOME,
    )
    payment_method = serializers.ChoiceField(
        choices=models.Order.PAYMENT_METHOD_CHOICES,
        default=models.Order.PAYMENT_METHOD_RAZORPAY,
    )
    shipping_details = ShippingDetailSerializer(required=False, allow_null=True)

    def validate_cart_id(self, value):
        if not models.Cart.objects.filter(pk=value).exists():
            raise serializers.ValidationError("No Cart with given id exists.")
        elif not models.CartItem.objects.filter(cart_id=value).exists():
            raise serializers.ValidationError("The Cart is empty.")
        return value

    def validate(self, data):
        delivery_method = data.get("delivery_method", models.Order.DELIVERY_METHOD_HOME)
        shipping_details = data.get("shipping_details", None)
        if (
            delivery_method == models.Order.DELIVERY_METHOD_HOME
            and not shipping_details
        ):
            raise serializers.ValidationError(
                "Shipping details are required for home delivery."
            )
        return data

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data.get("cart_id")
            shipping_data = self.validated_data.get("shipping_details")
            delivery_method = self.validated_data.get("delivery_method")
            payment_method = self.validated_data.get(
                "payment_method", models.Order.PAYMENT_METHOD_RAZORPAY
            )
            shipping_obj = None
            if delivery_method == models.Order.DELIVERY_METHOD_HOME:
                shipping_obj = models.ShippingDetail.objects.create(**shipping_data)
            order = models.Order.objects.create(
                user=self.context["user"],
                shipping_details=shipping_obj,
                delivery_method=delivery_method,
                payment_method=payment_method,
            )
            order.delivery_charge = order.get_delivery_charge(delivery_method)
            cart_items = models.CartItem.objects.select_related("product").filter(
                cart_id=cart_id
            )
            order_items = [
                models.OrderItem(
                    order=order, product=item.product, quantity=item.quantity
                )
                for item in cart_items
            ]

            for item in cart_items:
                item.product.consume_stock(item.quantity)

            models.OrderItem.objects.bulk_create(order_items)
            order.total_price = order.get_total_price()

            if payment_method == models.Order.PAYMENT_METHOD_RAZORPAY:
                client = razorpay.Client(
                    auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET)
                )
                razorpay_order = client.order.create(
                    {
                        "amount": int(order.total_price * 100),  # Amount in paise
                        "currency": "INR",
                        "payment_capture": 1,  # Auto capture
                    }
                )
                order.razorpay_order_id = razorpay_order["id"]
            order.save()

            models.Cart.objects.get(pk=cart_id).delete()

            return order


class RazorpayPaymentVerifySerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
