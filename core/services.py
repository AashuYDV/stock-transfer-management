from django.db import transaction

from .models import Product, Transfer, Warehouse, WarehouseStock


class InsufficientStockError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


class InvalidTransferError(Exception):
    pass


def create_transfer(
    source_warehouse_id: int,
    destination_warehouse_id: int,
    product_id: int,
    quantity: int,
) -> Transfer:
    if source_warehouse_id == destination_warehouse_id:
        raise InvalidTransferError("Source and destination warehouse must differ")
    if quantity <= 0:
        raise InvalidTransferError("Quantity must be greater than zero")

    source = Warehouse.objects.get(id=source_warehouse_id)
    destination = Warehouse.objects.get(id=destination_warehouse_id)
    product = Product.objects.get(id=product_id)

    available = (
        WarehouseStock.objects.filter(warehouse=source, product=product)
        .values_list("quantity", flat=True)
        .first()
        or 0
    )
    if available < quantity:
        raise InsufficientStockError(
            f"Insufficient stock: {available} available at {source.name}, {quantity} requested"
        )

    return Transfer.objects.create(
        source_warehouse=source,
        destination_warehouse=destination,
        product=product,
        quantity=quantity,
        status=Transfer.Status.PENDING,
    )


@transaction.atomic
def complete_transfer(transfer_id: int) -> Transfer:
    transfer = Transfer.objects.select_for_update().get(id=transfer_id)
    if transfer.status != Transfer.Status.PENDING:
        raise InvalidTransitionError(
            f"Cannot complete a transfer in status {transfer.status}"
        )

    source_stock = WarehouseStock.objects.select_for_update().filter(
        warehouse=transfer.source_warehouse, product=transfer.product
    ).first()
    available = source_stock.quantity if source_stock else 0
    if available < transfer.quantity:
        raise InsufficientStockError(
            f"Insufficient stock at {transfer.source_warehouse.name} to complete transfer"
        )

    source_stock.quantity -= transfer.quantity
    source_stock.save(update_fields=["quantity"])

    dest_stock, _ = WarehouseStock.objects.select_for_update().get_or_create(
        warehouse=transfer.destination_warehouse,
        product=transfer.product,
        defaults={"quantity": 0},
    )
    dest_stock.quantity += transfer.quantity
    dest_stock.save(update_fields=["quantity"])

    transfer.status = Transfer.Status.COMPLETED
    transfer.save(update_fields=["status", "updated_at"])
    return transfer


@transaction.atomic
def cancel_transfer(transfer_id: int) -> Transfer:
    transfer = Transfer.objects.select_for_update().get(id=transfer_id)
    if transfer.status != Transfer.Status.PENDING:
        raise InvalidTransitionError(
            f"Cannot cancel a transfer in status {transfer.status}"
        )
    transfer.status = Transfer.Status.CANCELLED
    transfer.save(update_fields=["status", "updated_at"])
    return transfer
