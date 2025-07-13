from django.db import transaction
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, views
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from . import models, serializers, permissions, pagination, filters, services


class ProductViewSet(viewsets.ModelViewSet):
    pagination_class = pagination.DefaultPagination
    permission_classes = [permissions.IsAdminOrReadOnly]
    filter_backends = [OrderingFilter, SearchFilter, DjangoFilterBackend]
    filterset_class = filters.ProductFilter

    search_fields = ["name"]
    ordering_fields = ["net_price", "name", "created_at"]
    ordering = ["created_at", "net_price"]
    lookup_field = "slug"

    def get_queryset(self):
        return models.Product.objects.all()

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT"]:
            return serializers.CreateProductSerializer
        return serializers.ProductSerializer

    def get_serializer_context(self):
        return {"request": self.request}


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.CartSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = pagination.DefaultPagination

    def get_queryset(self):
        if self.request.user.is_staff:
            return (
                models.Cart.objects.prefetch_related("cart_items__product")
                .all()
                .order_by("user__id")
            )
        return models.Cart.objects.prefetch_related("cart_items__product").filter(
            user_id=self.request.user.id
        )


class CartItemViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = pagination.DefaultPagination

    def get_queryset(self):
        return models.CartItem.objects.select_related("product").filter(
            cart_id=self.kwargs["cart_pk"]
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.AddCartItemSerializer
        elif self.request.method == "PATCH":
            return serializers.UpdateCartItemSerializer
        return serializers.CartItemSerializer

    def get_serializer_context(self):
        return {"cart_id": self.kwargs["cart_pk"], "request": self.request}


class OrderViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]
    pagination_class = pagination.DefaultPagination
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["placed_at"]
    filterset_fields = [
        "payment_status",
        "order_status",
        "delivery_method",
        "payment_method",
    ]

    def create(self, request, *args, **kwargs):

        serializer = serializers.CreateOrderSerializer(
            data=request.data,
            context={"user": self.request.user, "request": self.request},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = serializers.OrderSerializer(
            order, context={"request": self.request}
        )
        return Response(serializer.data)

    def get_queryset(self):
        queryset = (
            models.Order.objects.prefetch_related("order_items__product")
            .select_related("shipping_details")
            .all()
            .order_by("-placed_at")
        )
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user_id=self.request.user.id)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.CreateOrderSerializer
        elif self.request.method == "PATCH":
            return serializers.UpdateOrderSerializer
        return serializers.OrderSerializer

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class DispatchOrderView(views.APIView):
    def post(self, request, id):
        try:
            order = models.Order.objects.get(id=id)
        except models.Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to dispatch this item"},
                status=403,
            )

        if (
            order.payment_method == models.Order.PAYMENT_METHOD_RAZORPAY
            and order.payment_status != models.Order.PAYMENT_STATUS_SUCCESSFUL
        ):
            return Response(
                {"error": "This order has still pending payment"}, status=400
            )

        if order.order_status != models.Order.ORDER_STATUS_PROCESSING:
            return Response(
                {"error": "This order has already been dispatched or cancelled"},
                status=400,
            )

        order.update_order_status(models.Order.ORDER_STATUS_DISPATCHED)
        return Response({"message": "Order has been dispatched"}, status=200)


class CancelOrderView(views.APIView):
    def post(self, request, id):
        try:
            order = models.Order.objects.get(id=id)
        except models.Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.user != request.user:
            return Response(
                {"error": "You do not have permission to delete this order"}, status=403
            )

        if not order.can_be_cancelled():
            return Response({"error": "Order can not be cancelled now"}, status=400)

        with transaction.atomic():
            if order.can_be_refunded():
                response = services.refund_payment(order)
                if not response["success"]:
                    order.mark_refund_failed()
                    return Response({{"error": "Cancellation failed"}}, status=500)

                refund_id = response["refund"]["id"]
                order.mark_as_refunded(refund_id)
            elif order.payment_status == models.Order.PAYMENT_STATUS_PENDING:
                order.mark_payment_as_failed()
            order.cancel()
            order_items = models.OrderItem.objects.filter(order=order)
            for item in order_items:
                item.product.restore_stock(item.quantity)
            return Response({"message": "Order cancelled"}, status=200)


class RazorpayPaymentVerifyView(views.APIView):
    def post(self, request, id):
        serializer = serializers.RazorpayPaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            order = models.Order.objects.get(
                id=id, razorpay_order_id=data["razorpay_order_id"]
            )
        except models.Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.user != request.user:
            return Response(
                {"error": "You do not have permission to verify this order"}, status=403
            )

        if order.payment_status != models.Order.PAYMENT_STATUS_PENDING:
            return Response(
                {"error": "Payment for this order has already been verified or failed"},
                status=400,
            )

        is_verified = services.verify_razorpay_signature(data, order)

        if is_verified:
            order_items = models.OrderItem.objects.filter(order=order)
            delivered = True
            for item in order_items:
                if not item.product.is_digital:
                    delivered = False
                    break
            if delivered:
                order.mark_as_completed()
            return Response({"message": "Payment verified successfully"}, status=200)
        else:
            return Response({"error": "Payment verification failed"}, status=400)


class RetryRazorpayPaymentView(views.APIView):
    def post(self, request, id):
        try:
            order = models.Order.objects.get(id=id, user=request.user)
        except models.Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.payment_status != order.PAYMENT_STATUS_PENDING:
            return Response({"error": "Order is not eligible for retry"}, status=400)

        if order.payment_method != order.PAYMENT_METHOD_RAZORPAY:
            return Response(
                {"error": "Only online payments can be retried"}, status=400
            )

        razorpay_order = services.create_razorpay_order(order)
        order.razorpay_order_id = razorpay_order["id"]
        order.payment_status = models.Order.PAYMENT_STATUS_PENDING
        order.save()

        return Response(
            {
                "razorpay_order_id": razorpay_order["id"],
                "amount": razorpay_order["amount"],
                "currency": razorpay_order["currency"],
                "key": settings.RAZORPAY_API_KEY,
            },
            200,
        )


class AcceptOrderView(views.APIView):
    def post(self, request, id):
        try:
            order = models.Order.objects.get(id=id, user=request.user)
        except models.Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.payment_status != models.Order.PAYMENT_STATUS_SUCCESSFUL:
            return Response(
                {
                    "error": "You cannot accept the order untill you complete the payment"
                },
                status=400,
            )

        if order.order_status in [
            models.Order.ORDER_STATUS_CANCELLED,
            models.Order.ORDER_STATUS_COMPLETED,
        ]:
            return Response(
                {"error": "The order is either already recieved or has been cancelled"},
                status=400,
            )

        order.mark_as_completed()

        return Response(
            {"message": "Your order was completed successfully"}, status=200
        )
