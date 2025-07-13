from django.conf import settings
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter
from . import views


def get_product_viewset():
    view_path = settings.STORE_APP.get("PRODUCT_VIEWSET")
    if view_path:
        from django.utils.module_loading import import_string

        return import_string(view_path)
    return views.ProductViewSet


router = DefaultRouter()

router.register("products", get_product_viewset(), basename="products")
router.register("carts", views.CartViewSet, basename="carts")
router.register("orders", views.OrderViewSet, basename="orders")

cart_router = NestedSimpleRouter(router, "carts", lookup="cart")
cart_router.register("items", views.CartItemViewSet, basename="cart-items")


urlpatterns = router.urls + cart_router.urls
urlpatterns += [
    path(
        "orders/<int:id>/verify-payment/",
        views.RazorpayPaymentVerifyView.as_view(),
        name="verify-payment",
    ),
    path(
        "orders/<int:id>/cancel/",
        views.CancelOrderView.as_view(),
        name="cancel-order",
    ),
    path(
        "orders/<int:id>/retry-payment/",
        views.RetryRazorpayPaymentView.as_view(),
        name="retry-payment",
    ),
    path(
        "orders/<int:id>/accept-order/",
        views.AcceptOrderView.as_view(),
        name="accept-order",
    ),
    path(
        "orders/<int:id>/dispatch/",
        views.DispatchOrderView.as_view(),
        name="dispatch-order",
    ),
]
