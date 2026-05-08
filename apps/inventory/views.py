from rest_framework import viewsets
from apps.inventory.models import StockItem, Offcut
from apps.inventory.serializers import StockItemSerializer, OffcutSerializer


class StockItemViewSet(viewsets.ModelViewSet):
    queryset = StockItem.objects.select_related("product", "product__extrusion", "bin_location", "company")
    serializer_class = StockItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(state=state)
        product = self.request.query_params.get("product")
        if product:
            qs = qs.filter(product_id=product)
        company = self.request.query_params.get("company")
        if company:
            qs = qs.filter(company_id=company)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        return qs


class OffcutViewSet(viewsets.ModelViewSet):
    queryset = Offcut.objects.select_related("product", "product__extrusion", "bin_location", "company")
    serializer_class = OffcutSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        is_reserved = self.request.query_params.get("is_reserved")
        if is_reserved is not None:
            qs = qs.filter(is_reserved=is_reserved.lower() == "true")
        product = self.request.query_params.get("product")
        if product:
            qs = qs.filter(product_id=product)
        company = self.request.query_params.get("company")
        if company:
            qs = qs.filter(company_id=company)
        return qs