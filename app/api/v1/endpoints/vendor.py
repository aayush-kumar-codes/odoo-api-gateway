from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.vendor import Vendor, VendorCreate, VendorUpdate
from app.models.vendor import Vendor as VendorModel
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, clear_cache_pattern
from app.api.deps import cache_response
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

# Standard error messages
VENDOR_NOT_FOUND = "Vendor not found"
UNAUTHORIZED = "Not enough permissions"
VENDOR_EXISTS = "Vendor already exists"

@router.get("/", response_model=List[Vendor])
@cache_response(expire=1800, key_prefix="vendors")  # Cache for 30 minutes
async def get_vendors(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all vendors.
    """
    try:
        current_user = await deps.get_current_user(credentials, db)
        
        cache_key = f"vendor:list:{skip}:{limit}"
        cached_data = get_cache(cache_key)
        if cached_data:
            return cached_data
            
        vendors = db.query(VendorModel).offset(skip).limit(limit).all()
        set_cache(cache_key, vendors, expire=1800)
        return vendors
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving vendors: {str(e)}"
        )

@router.get("/{vendor_id}", response_model=Vendor)
@cache_response(expire=1800, key_prefix="vendor")
async def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Get details of a specific vendor.
    """
    current_user = await deps.get_current_user(credentials, db)
    
    vendor = db.query(VendorModel).filter(VendorModel.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

@router.post("/", response_model=Vendor)
async def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Add a new vendor (admin only).
    """
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Superuser required."
        )
    
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
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Update vendor details (admin only).
    """
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Superuser required."
        )
    
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
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Remove a vendor (admin only).
    """
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Superuser required."
        )
    
    db_vendor = db.query(VendorModel).filter(VendorModel.id == vendor_id).first()
    if not db_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    db.delete(db_vendor)
    db.commit()
    
    # Clear vendor caches
    clear_cache_pattern("vendors:*")
    clear_cache_pattern(f"vendor:get_vendor:{vendor_id}")
    
    return {"message": "Vendor deleted successfully"} 