from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.attribute import Attribute, AttributeCreate
from app.models.attribute import ProductAttribute
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, delete_cache, clear_cache_pattern
from app.schemas.attribute_value import AttributeValue, AttributeValueCreate
from app.models.attribute_value import ProductAttributeValue
from fastapi.security import HTTPAuthorizationCredentials
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[Attribute])
async def get_attributes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Security(deps.get_current_user)
):
    """
    Retrieve all attributes.
    """
    cache_key = f"attributes:{skip}:{limit}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data
    
    attributes = db.query(ProductAttribute).offset(skip).limit(limit).all()
    set_cache(cache_key, attributes, expire=3600)
    return attributes

@router.get("/{attribute_id}", response_model=Attribute)
async def get_attribute(
    attribute_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Security(deps.get_current_user)
):
    """
    Get a specific attribute by ID.
    """
    cache_key = f"attribute:{attribute_id}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data
    
    attribute = db.query(ProductAttribute).filter(ProductAttribute.id == attribute_id).first()
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    set_cache(cache_key, attribute, expire=3600)
    return attribute

@router.post("/", response_model=Attribute)
async def create_attribute(
    attribute: AttributeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Security(deps.get_current_superuser)
):
    """
    Create a new attribute (admin only).
    """
    db_attribute = ProductAttribute(**attribute.dict())
    db.add(db_attribute)
    db.commit()
    db.refresh(db_attribute)
    
    delete_cache("attributes:*")
    return db_attribute

@router.put("/{attribute_id}", response_model=Attribute)
async def update_attribute(
    attribute_id: int,
    attribute: AttributeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Security(deps.get_current_superuser)
):
    """
    Update an attribute (admin only).
    """
    db_attribute = db.query(ProductAttribute).filter(ProductAttribute.id == attribute_id).first()
    if not db_attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    for key, value in attribute.dict().items():
        setattr(db_attribute, key, value)
    
    db.commit()
    db.refresh(db_attribute)
    
    delete_cache(f"attribute:{attribute_id}")
    delete_cache("attributes:*")
    return db_attribute

@router.delete("/{attribute_id}")
async def delete_attribute(
    attribute_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Security(deps.get_current_superuser)
):
    """
    Delete an attribute (admin only).
    """
    db_attribute = db.query(ProductAttribute).filter(ProductAttribute.id == attribute_id).first()
    if not db_attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    db.delete(db_attribute)
    db.commit()
    
    delete_cache(f"attribute:{attribute_id}")
    delete_cache("attributes:*")
    return {"message": "Attribute deleted successfully"}

@router.get("/{attribute_id}/values", response_model=List[AttributeValue])
async def get_attribute_values(
    attribute_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all values for a specific attribute.
    """
    cache_key = f"attribute:{attribute_id}:values:{skip}:{limit}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data
    
    values = db.query(ProductAttributeValue)\
        .filter(ProductAttributeValue.attribute_id == attribute_id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    set_cache(cache_key, values, expire=3600)
    return values

@router.post("/{attribute_id}/values", response_model=AttributeValue)
async def create_attribute_value(
    attribute_id: int,
    value: AttributeValueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new attribute value.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Check if attribute exists
    attribute = db.query(ProductAttribute).filter(ProductAttribute.id == attribute_id).first()
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")

    # Create new attribute value
    db_value = ProductAttributeValue(
        name=value.value,  # Use value as name
        value=value.value,
        display_value=value.display_value,
        attribute_id=attribute_id,
        sequence=value.sequence if hasattr(value, 'sequence') else 0,
        is_custom=value.is_custom if hasattr(value, 'is_custom') else False,
        variant_id=value.variant_id if hasattr(value, 'variant_id') else None
    )
    
    db.add(db_value)
    db.commit()
    db.refresh(db_value)

    # Clear cache
    clear_cache_pattern(f"attribute:{attribute_id}:values:*")
    
    return db_value

@router.put("/{attribute_id}/values/{value_id}", response_model=AttributeValue)
async def update_attribute_value(
    attribute_id: int,
    value_id: int,
    value: AttributeValueCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Update an attribute value.
    """
    # Get current user and verify superuser status
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Superuser required."
        )
    
    db_value = db.query(ProductAttributeValue)\
        .filter(
            ProductAttributeValue.id == value_id,
            ProductAttributeValue.attribute_id == attribute_id
        ).first()
    
    if not db_value:
        raise HTTPException(status_code=404, detail="Attribute value not found")
    
    for key, val in value.dict().items():
        setattr(db_value, key, val)
    
    db.commit()
    db.refresh(db_value)
    
    delete_cache(f"attribute:{attribute_id}:values:*")
    return db_value

@router.delete("/{attribute_id}/values/{value_id}")
async def delete_attribute_value(
    attribute_id: int,
    value_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete an attribute value.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_value = db.query(ProductAttributeValue)\
        .filter(
            ProductAttributeValue.id == value_id,
            ProductAttributeValue.attribute_id == attribute_id
        ).first()
    
    if not db_value:
        raise HTTPException(status_code=404, detail="Attribute value not found")
    
    db.delete(db_value)
    db.commit()
    
    delete_cache(f"attribute:{attribute_id}:values:*")
    return {"message": "Attribute value deleted successfully"} 