from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from store.pagination import DefaultPagination
from . import serializers, models


class ReviewViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "patch", "delete"]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ["created_at", "rating"]
    filterset_fields = ["rating"]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        return models.Review.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.CreateReviewSerializer
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.UpdateReviewSerializer
        return serializers.ReviewSerializer
