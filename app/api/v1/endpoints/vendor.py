from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.vendor import Vendor, VendorCreate, VendorUpdate
from app.models.vendor import Vendor as VendorModel
from app.models.user import User
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, clear_cache_pattern
from app.api.deps import cache_response

router = APIRouter()

@router.get("/", response_model=List[Vendor])
@cache_response(expire=1800, key_prefix="vendors")  # Cache for 30 minutes
async def get_vendors(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Retrieve all vendors.
    """
    vendors = db.query(VendorModel).offset(skip).limit(limit).all()
    return vendors

@router.get("/{vendor_id}", response_model=Vendor)
@cache_response(expire=1800, key_prefix="vendor")
async def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get details of a specific vendor.
    """
    vendor = db.query(VendorModel).filter(VendorModel.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

@router.post("/", response_model=Vendor)
async def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Add a new vendor (admin only).
    """
    db_vendor = VendorModel(**vendor.dict())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    
    # Clear vendor caches
    clear_cache_pattern("vendors:*")
    return db_vendor

@router.put("/{vendor_id}", response_model=Vendor)
async def update_vendor(
    vendor_id: int,
    vendor: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Update vendor details (admin only).
    """
    db_vendor = db.query(VendorModel).filter(VendorModel.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    for key, value in vendor.dict(exclude_unset=True).items():
        setattr(db_vendor, key, value)
    
    db.commit()
    db.refresh(db_vendor)
    
    # Clear vendor caches
    clear_cache_pattern("vendors:*")
    clear_cache_pattern(f"vendor:get_vendor:{vendor_id}")
    
    return db_vendor

@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Remove a vendor (admin only).
    """
    db_vendor = db.query(VendorModel).filter(VendorModel.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    db.delete(db_vendor)
    db.commit()
    
    # Clear vendor caches
    clear_cache_pattern("vendors:*")
    clear_cache_pattern(f"vendor:get_vendor:{vendor_id}")
    
    return {"message": "Vendor deleted successfully"} 