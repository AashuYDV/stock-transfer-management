from fastapi import APIRouter, HTTPException

from core.models import Product

from ..schemas import ProductCreate, ProductOut

router = APIRouter(prefix="/api/products", tags=["products"])


@router.post("", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate):
    if Product.objects.filter(sku=payload.sku).exists():
        raise HTTPException(status_code=400, detail="A product with this SKU already exists")
    product = Product.objects.create(name=payload.name, sku=payload.sku)
    return ProductOut(id=product.id, name=product.name, sku=product.sku)


@router.get("", response_model=list[ProductOut])
def list_products():
    return [
        ProductOut(id=p.id, name=p.name, sku=p.sku) for p in Product.objects.all()
    ]
