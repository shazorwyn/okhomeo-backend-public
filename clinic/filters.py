import django_filters
from .models import Disease, Category


class DiseaseFilter(django_filters.FilterSet):
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        to_field_name="slug",
        label="Category",
    )

    class Meta:
        model = Disease
        fields = ["category"]
