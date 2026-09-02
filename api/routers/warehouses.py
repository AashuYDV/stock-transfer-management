from fastapi import APIRouter, HTTPException

from core.models import Warehouse, WarehouseStock

from core.models import Product

from ..schemas import StockOut, StockSet, WarehouseCreate, WarehouseOut

router = APIRouter(prefix="/api/warehouses", tags=["warehouses"])


@router.post("", response_model=WarehouseOut, status_code=201)
def create_warehouse(payload: WarehouseCreate):
    if Warehouse.objects.filter(name=payload.name).exists():
        raise HTTPException(status_code=400, detail="A warehouse with this name already exists")
    warehouse = Warehouse.objects.create(name=payload.name, location=payload.location)
    return WarehouseOut(id=warehouse.id, name=warehouse.name, location=warehouse.location)


@router.get("", response_model=list[WarehouseOut])
def list_warehouses():
    return [
        WarehouseOut(id=w.id, name=w.name, location=w.location)
        for w in Warehouse.objects.all()
    ]


@router.get("/{warehouse_id}/stock", response_model=list[StockOut])
def get_warehouse_stock(warehouse_id: int):
    if not Warehouse.objects.filter(id=warehouse_id).exists():
        raise HTTPException(status_code=404, detail="Warehouse not found")
    stock = WarehouseStock.objects.filter(warehouse_id=warehouse_id).select_related("product")
    return [
        StockOut(
            product_id=s.product.id,
            product_name=s.product.name,
            sku=s.product.sku,
            quantity=s.quantity,
        )
        for s in stock
    ]


@router.put("/{warehouse_id}/stock", response_model=StockOut)
def set_warehouse_stock(warehouse_id: int, payload: StockSet):
    if not Warehouse.objects.filter(id=warehouse_id).exists():
        raise HTTPException(status_code=404, detail="Warehouse not found")
    if not Product.objects.filter(id=payload.product_id).exists():
        raise HTTPException(status_code=404, detail="Product not found")

    stock, _ = WarehouseStock.objects.update_or_create(
        warehouse_id=warehouse_id,
        product_id=payload.product_id,
        defaults={"quantity": payload.quantity},
    )
    return StockOut(
        product_id=stock.product.id,
        product_name=stock.product.name,
        sku=stock.product.sku,
        quantity=stock.quantity,
    )
