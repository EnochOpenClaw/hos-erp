"""
Sales: Customers, Quotes, Sales Orders.
"""
from django.db import models
import uuid
from apps.core.models import TimestampedModel, Company


class Customer(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="customers")
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [["company", "code"]]

    def __str__(self):
        return self.name


class Quote(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="quotes")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name="quotes")
    quote_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    ], default="draft")
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["company", "quote_number"]]

    def __str__(self):
        return f"Quote {self.quote_number}"


class QuoteLine(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=500)
    product = models.ForeignKey(
        "products.Product", on_delete=models.SET_NULL, null=True, blank=True
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ["id"]


class SalesOrder(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sales_orders")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name="sales_orders")
    order_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("manufacturing", "In Manufacturing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ], default="pending")
    order_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["company", "order_number"]]

    def __str__(self):
        return f"Order {self.order_number}"


class SalesOrderLine(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=500)
    product = models.ForeignKey(
        "products.Product", on_delete=models.SET_NULL, null=True, blank=True
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ["id"]
