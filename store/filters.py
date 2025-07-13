import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    # Filter by content_type's model name (case-insensitive)
    type = django_filters.CharFilter(
        field_name="content_type__model", lookup_expr="iexact"
    )
    min_price = django_filters.NumberFilter(field_name="net_price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="net_price", lookup_expr="lte")

    class Meta:
        model = Product
        fields = ["trending"]
