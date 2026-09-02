import pytest

from core import services
from core.models import Product, Transfer, Warehouse, WarehouseStock


def _setup_basic():
    wh1 = Warehouse.objects.create(name="WH1", location="A")
    wh2 = Warehouse.objects.create(name="WH2", location="B")
    product = Product.objects.create(name="Widget", sku="W-1")
    WarehouseStock.objects.create(warehouse=wh1, product=product, quantity=50)
    return wh1, wh2, product


def test_create_transfer_success():
    wh1, wh2, product = _setup_basic()
    transfer = services.create_transfer(wh1.id, wh2.id, product.id, 10)
    assert transfer.status == Transfer.Status.PENDING
    assert transfer.quantity == 10


def test_create_transfer_insufficient_stock():
    wh1, wh2, product = _setup_basic()
    with pytest.raises(services.InsufficientStockError):
        services.create_transfer(wh1.id, wh2.id, product.id, 999)


def test_create_transfer_same_warehouse():
    wh1, _, product = _setup_basic()
    WarehouseStock.objects.filter(warehouse=wh1, product=product).update(quantity=100)
    with pytest.raises(services.InvalidTransferError):
        services.create_transfer(wh1.id, wh1.id, product.id, 5)


def test_complete_transfer_moves_stock():
    wh1, wh2, product = _setup_basic()
    transfer = services.create_transfer(wh1.id, wh2.id, product.id, 20)
    services.complete_transfer(transfer.id)

    transfer.refresh_from_db()
    assert transfer.status == Transfer.Status.COMPLETED

    source_qty = WarehouseStock.objects.get(warehouse=wh1, product=product).quantity
    dest_qty = WarehouseStock.objects.get(warehouse=wh2, product=product).quantity
    assert source_qty == 30
    assert dest_qty == 20


def test_cancel_transfer_does_not_move_stock():
    wh1, wh2, product = _setup_basic()
    transfer = services.create_transfer(wh1.id, wh2.id, product.id, 20)
    services.cancel_transfer(transfer.id)

    transfer.refresh_from_db()
    assert transfer.status == Transfer.Status.CANCELLED
    assert WarehouseStock.objects.get(warehouse=wh1, product=product).quantity == 50
    assert not WarehouseStock.objects.filter(warehouse=wh2, product=product).exists()


def test_cannot_complete_twice():
    wh1, wh2, product = _setup_basic()
    transfer = services.create_transfer(wh1.id, wh2.id, product.id, 20)
    services.complete_transfer(transfer.id)
    with pytest.raises(services.InvalidTransitionError):
        services.complete_transfer(transfer.id)


def test_cannot_cancel_completed_transfer():
    wh1, wh2, product = _setup_basic()
    transfer = services.create_transfer(wh1.id, wh2.id, product.id, 20)
    services.complete_transfer(transfer.id)
    with pytest.raises(services.InvalidTransitionError):
        services.cancel_transfer(transfer.id)
