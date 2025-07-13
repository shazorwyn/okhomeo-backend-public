from django.conf import settings
from django.core.mail import send_mail
from django.contrib.contenttypes.models import ContentType
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from store.models import Product
from feedback.models import Review
from feedback.views import ReviewViewSet as FeedbackReviewViewSet
from .serializers import (
    CreateProductReviewSerializer,
    ProductReviewSerializer,
    ContactSerializer,
)
from .models import User


class ProductReviewViewSet(FeedbackReviewViewSet):
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["content_type"] = ContentType.objects.get_for_model(Product)
        slug = self.kwargs.get("product_slug")
        if not slug:
            raise ValueError("Product slug is required to fetch reviews.")
        try:
            product = Product.objects.get(slug=slug)
            context["object_id"] = product.id
        except Product.DoesNotExist:
            raise ValueError(f"Product with slug '{slug}' does not exist.")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        product_slug = self.kwargs.get("product_slug")
        models = [cls.model_class() for cls in Review.get_allowed_content_types()]
        if Product not in models:
            raise ValueError("Product is not a valid content type for reviews.")
        if product_slug:
            print(f"Filtering reviews for product slug: {product_slug}")
            try:
                obj = Product.objects.get(slug=product_slug)
                ct = ContentType.objects.get_for_model(Product)
                return queryset.filter(content_type=ct, object_id=obj.id)
            except Product.DoesNotExist:
                return queryset.none()
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateProductReviewSerializer
        if self.request.method in ["PUT", "PATCH"]:
            return super().get_serializer_class()
        return ProductReviewSerializer


class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access = response.data["access"]
            refresh = response.data["refresh"]

            response.set_cookie(
                key="access",
                value=access,
                httponly=True,
                secure=True,
                samesite="None",
                max_age=5 * 60,  # ACCESS_TOKEN_LIFETIME=5min
            )
            response.set_cookie(
                key="refresh",
                value=refresh,
                httponly=True,
                secure=True,
                samesite="None",
                max_age=1 * 24 * 60 * 60,  # REFRESH_TOKEN_LIFETIME=1day
            )

        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh")
        if refresh_token:
            request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access = response.data["access"]

            response.set_cookie(
                key="access",
                value=access,
                httponly=True,
                secure=True,
                samesite="None",
                max_age=5 * 60,  # ACCESS_TOKEN_LIFETIME=5min
            )

        return response


class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access",
            value="none",
            httponly=True,
            secure=True,
            samesite="None",
            max_age=0,
        )
        response.set_cookie(
            key="refresh",
            value="none",
            httponly=True,
            secure=True,
            samesite="None",
            max_age=0,
        )
        return response


class MakeStaffView(APIView):
    def post(self, request, id):
        if not request.user.is_superuser:
            return Response(
                {"error": "You don't have permission to make staff"}, status=403
            )

        user = User.objects.get(id=id)
        if not user:
            return Response({"error": "User with given id does not exist"}, status=400)

        user.is_staff = True
        user.save()
        return Response({"message": f"User-{id} is now a staff"}, status=200)


class ContactView(APIView):
    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            send_mail(
                subject="New Contact Message",
                message=f"From: {data['name']} <{data['email']}>\n\n{data['message']}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
            )
            return Response({"detail": "Message sent successfully."}, status=200)
        return Response(serializer.errors, status=400)
