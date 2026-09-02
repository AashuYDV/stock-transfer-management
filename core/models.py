from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Warehouse(models.Model):
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WarehouseStock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stock")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock")
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("warehouse", "product")
        ordering = ["warehouse__name", "product__name"]

    def __str__(self):
        return f"{self.warehouse} / {self.product}: {self.quantity}"


class Transfer(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    source_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="outgoing_transfers"
    )
    destination_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="incoming_transfers"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="transfers")
    quantity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Transfer #{self.pk}: {self.product} x{self.quantity} ({self.status})"
