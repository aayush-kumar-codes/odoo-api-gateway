from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.product import ProductVariant, ProductVariantCreate, ProductAttributeValue
from app.models.variant import ProductVariant as VariantModel
from app.models.user import User
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, delete_cache

router = APIRouter()

@router.get("/", response_model=List[ProductVariant])
async def get_variants(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve all variants.
    """
    cache_key = f"variants:{skip}:{limit}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data
    
    variants = db.query(VariantModel).offset(skip).limit(limit).all()
    set_cache(cache_key, variants, expire=1800)
    return variants

@router.get("/{variant_id}", response_model=ProductVariant)
async def get_variant(
    variant_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific variant by ID.
    """
    cache_key = f"variant:{variant_id}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data
    
    variant = db.query(VariantModel).filter(VariantModel.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    set_cache(cache_key, variant, expire=1800)
    return variant

@router.post("/", response_model=ProductVariant)
async def create_variant(
    variant: ProductVariantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Create a new product variant
    """
    db_variant = ProductVariantModel(
        product_id=variant.product_id,
        sku=variant.sku,
        price=variant.price,
        barcode=variant.barcode,
        price_extra=variant.price_extra
    )
    db.add(db_variant)
    db.commit()
    db.refresh(db_variant)
    
    # Add attribute values
    for attr_value in variant.attribute_values:
        db_attr_value = ProductAttributeValue(
            attribute_id=attr_value.attribute_id,
            name=attr_value.name,
            variant_id=db_variant.id
        )
        db.add(db_attr_value)
    
    db.commit()
    db.refresh(db_variant)
    
    # Clear caches
    delete_cache(f"product:{variant.product_id}")
    delete_cache("products:*")
    return db_variant

@router.put("/{variant_id}", response_model=ProductVariant)
async def update_variant(
    variant_id: int,
    variant: ProductVariant,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update a variant (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_variant = db.query(VariantModel).filter(VariantModel.id == variant_id).first()
    if not db_variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    for key, value in variant.dict().items():
        setattr(db_variant, key, value)
    
    db.commit()
    db.refresh(db_variant)
    
    delete_cache(f"variant:{variant_id}")
    delete_cache("variants:*")
    return db_variant

@router.delete("/{variant_id}")
async def delete_variant(
    variant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete a variant (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_variant = db.query(VariantModel).filter(VariantModel.id == variant_id).first()
    if not db_variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    db.delete(db_variant)
    db.commit()
    
    delete_cache(f"variant:{variant_id}")
    delete_cache("variants:*")
    return {"message": "Variant deleted successfully"} 