from django.db.models import Q
from fastapi import APIRouter, HTTPException, Query

from core import services
from core.models import Product, Transfer, Warehouse

from ..schemas import TransferCreate, TransferOut, TransferStatusUpdate

router = APIRouter(prefix="/api/transfers", tags=["transfers"])


def _serialize(transfer: Transfer) -> TransferOut:
    return TransferOut(
        id=transfer.id,
        source_warehouse_id=transfer.source_warehouse_id,
        source_warehouse_name=transfer.source_warehouse.name,
        destination_warehouse_id=transfer.destination_warehouse_id,
        destination_warehouse_name=transfer.destination_warehouse.name,
        product_id=transfer.product_id,
        product_name=transfer.product.name,
        quantity=transfer.quantity,
        status=transfer.status,
        created_at=transfer.created_at,
        updated_at=transfer.updated_at,
    )


@router.post("", response_model=TransferOut, status_code=201)
def create_transfer(payload: TransferCreate):
    try:
        transfer = services.create_transfer(
            source_warehouse_id=payload.source_warehouse_id,
            destination_warehouse_id=payload.destination_warehouse_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )
    except Warehouse.DoesNotExist:
        raise HTTPException(status_code=404, detail="Source or destination warehouse not found")
    except Product.DoesNotExist:
        raise HTTPException(status_code=404, detail="Product not found")
    except (services.InvalidTransferError, services.InsufficientStockError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    transfer = Transfer.objects.select_related(
        "source_warehouse", "destination_warehouse", "product"
    ).get(id=transfer.id)
    return _serialize(transfer)


@router.get("", response_model=list[TransferOut])
def list_transfers(
    status: str | None = Query(default=None),
    warehouse_id: int | None = Query(default=None),
):
    qs = Transfer.objects.select_related(
        "source_warehouse", "destination_warehouse", "product"
    )
    if status:
        qs = qs.filter(status=status)
    if warehouse_id:
        qs = qs.filter(
            Q(source_warehouse_id=warehouse_id) | Q(destination_warehouse_id=warehouse_id)
        )
    return [_serialize(t) for t in qs]


@router.get("/{transfer_id}", response_model=TransferOut)
def get_transfer(transfer_id: int):
    try:
        transfer = Transfer.objects.select_related(
            "source_warehouse", "destination_warehouse", "product"
        ).get(id=transfer_id)
    except Transfer.DoesNotExist:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return _serialize(transfer)


@router.patch("/{transfer_id}/status", response_model=TransferOut)
def update_transfer_status(transfer_id: int, payload: TransferStatusUpdate):
    try:
        if payload.status == "COMPLETED":
            transfer = services.complete_transfer(transfer_id)
        else:
            transfer = services.cancel_transfer(transfer_id)
    except Transfer.DoesNotExist:
        raise HTTPException(status_code=404, detail="Transfer not found")
    except services.InsufficientStockError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except services.InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    transfer = Transfer.objects.select_related(
        "source_warehouse", "destination_warehouse", "product"
    ).get(id=transfer.id)
    return _serialize(transfer)
