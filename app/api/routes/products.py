from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.dependencies import get_session
from app.models.product_model import Product
from app.schemas.product_schema import (
    ProductCreate,
    ProductPublic,
    ProductUpdate,
)


router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{product_id}", response_model=ProductPublic)
async def read_product(
    *, session: Session = Depends(get_session), product_id: int
):
    db_product = session.get(Product, product_id)

    if db_product is None:
        raise HTTPException(404, "Product not found.")

    return db_product


@router.get("/", response_model=list[ProductPublic])
async def read_products(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    query = select(Product).offset(offset).limit(limit)
    db_products = session.exec(query).all()
    return db_products


@router.post("/", response_model=ProductPublic)
async def create_product(
    *, session: Session = Depends(get_session), product: ProductCreate
):
    db_product = Product.model_validate(product)

    session.add(db_product)
    session.commit()
    session.refresh(db_product)

    return db_product


@router.patch("/{product_id}", response_model=ProductPublic)
async def update_product(
    *,
    session: Session = Depends(get_session),
    product_id: int,
    product: ProductUpdate,
):
    db_product = session.get(Product, product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    product_data = product.model_dump(exclude_unset=True)
    db_product.sqlmodel_update(product_data)

    session.add(db_product)
    session.commit()
    session.refresh(db_product)

    return db_product
