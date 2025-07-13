from django.urls import path, include
from store.urls import router as store_router
from .views import ProductReviewViewSet, ContactView
from rest_framework_nested.routers import NestedSimpleRouter

product_router = NestedSimpleRouter(store_router, "products", lookup="product")
product_router.register("reviews", ProductReviewViewSet, basename="product-reviews")

urlpatterns = [
    path("clinic/", include("clinic.urls")),
    path("store/", include("store.urls")),
    path("store/", include(product_router.urls)),
]
