from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .serializers import *
from .permissions import IsAdminOrReadOnly
from .pagination import DefaultPagination
from .filters import DiseaseFilter


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination
    lookup_field = "slug"


class DiseaseViewSet(viewsets.ModelViewSet):
    queryset = Disease.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = DiseaseFilter
    search_fields = ["name"]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return CreateDiseaseSerializer
        return DiseaseSerializer


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["specializations"]
    search_fields = ["name"]


class TreatmentViewSet(viewsets.ModelViewSet):
    queryset = Treatment.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["disease"]
    search_fields = ["name"]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT"]:
            return CreateTreatmentSerializer
        return TreatmentSerializer


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_prescription_required"]
    search_fields = ["name"]
    ordering_fields = ["expiry_date"]
    lookup_field = "slug"


class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = DefaultPagination
