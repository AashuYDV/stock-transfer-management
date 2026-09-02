from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=64)


class ProductOut(BaseModel):
    id: int
    name: str
    sku: str


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str = ""


class WarehouseOut(BaseModel):
    id: int
    name: str
    location: str


class StockOut(BaseModel):
    product_id: int
    product_name: str
    sku: str
    quantity: int


class StockSet(BaseModel):
    product_id: int
    quantity: int = Field(ge=0)


class TransferCreate(BaseModel):
    source_warehouse_id: int
    destination_warehouse_id: int
    product_id: int
    quantity: int = Field(gt=0)


class TransferOut(BaseModel):
    id: int
    source_warehouse_id: int
    source_warehouse_name: str
    destination_warehouse_id: int
    destination_warehouse_name: str
    product_id: int
    product_name: str
    quantity: int
    status: str
    created_at: datetime
    updated_at: datetime


class TransferStatusUpdate(BaseModel):
    status: Literal["COMPLETED", "CANCELLED"]


class ErrorResponse(BaseModel):
    detail: str
