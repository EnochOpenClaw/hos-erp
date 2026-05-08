from rest_framework import viewsets
from apps.sales.models import Customer, Quote, SalesOrder
from apps.sales.serializers import (
    CustomerSerializer,
    QuoteSerializer,
    SalesOrderSerializer,
)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class QuoteViewSet(viewsets.ModelViewSet):
    queryset = Quote.objects.select_related("customer").prefetch_related("lines__product")
    serializer_class = QuoteSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        customer = self.request.query_params.get("customer")
        if customer:
            qs = qs.filter(customer_id=customer)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.select_related("customer").prefetch_related("lines__product")
    serializer_class = SalesOrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        customer = self.request.query_params.get("customer")
        if customer:
            qs = qs.filter(customer_id=customer)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs