from rest_framework import viewsets
from apps.products.models import MaterialCategory, ExtrusionType, Product
from apps.products.serializers import (
    MaterialCategorySerializer,
    ExtrusionTypeSerializer,
    ProductSerializer,
)


class MaterialCategoryViewSet(viewsets.ModelViewSet):
    queryset = MaterialCategory.objects.all()
    serializer_class = MaterialCategorySerializer


class ExtrusionTypeViewSet(viewsets.ModelViewSet):
    queryset = ExtrusionType.objects.all()
    serializer_class = ExtrusionTypeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "extrusion")
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category_id=category)
        extrusion = self.request.query_params.get("extrusion")
        if extrusion:
            qs = qs.filter(extrusion_id=extrusion)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(code__icontains=search)
        return qs