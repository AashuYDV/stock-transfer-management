from django.contrib import admin

from .models import Product, Transfer, Warehouse, WarehouseStock


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sku", "created_at")
    search_fields = ("name", "sku")


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "location", "created_at")
    search_fields = ("name", "location")


@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ("id", "warehouse", "product", "quantity")
    list_filter = ("warehouse", "product")


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "source_warehouse",
        "destination_warehouse",
        "product",
        "quantity",
        "status",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "source_warehouse", "destination_warehouse")
    readonly_fields = ("created_at", "updated_at")
