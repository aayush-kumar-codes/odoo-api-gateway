from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.product import Category, CategoryCreate, Product
from app.models.category import Category as CategoryModel
from app.models.product import Product as ProductModel
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, delete_cache
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

# Standard error messages
CATEGORY_NOT_FOUND = "Category not found"
UNAUTHORIZED = "Not enough permissions"

@router.get("/", response_model=List[Category])
async def get_categories(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security),
    skip: int = 0,
    limit: int = 100,
    vendor_id: Optional[int] = None,
    parent_id: Optional[int] = None
):
    """Retrieve categories with optional filtering"""
    try:
        current_user = await deps.get_current_user(credentials, db)
        
        cache_key = f"category:list:v{vendor_id}:p{parent_id}:{skip}:{limit}"
        cached_data = get_cache(cache_key)
        if cached_data:
            return cached_data
        
        query = db.query(CategoryModel)
        
        if vendor_id:
            query = query.filter(CategoryModel.vendor_id == vendor_id)
        if parent_id:
            query = query.filter(CategoryModel.parent_id == parent_id)
        
        categories = query.offset(skip).limit(limit).all()
        set_cache(cache_key, categories, expire=3600)
        return categories
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving categories: {str(e)}"
        )

@router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Get a specific category by ID.
    """
    # Verify authentication
    current_user = await deps.get_current_user(credentials, db)
    
    cache_key = f"category:{category_id}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data
    
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    set_cache(cache_key, category, expire=3600)
    return category

@router.post("/", response_model=Category)
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Create a new category (admin only).
    """
    # Verify authentication and superuser status
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Superuser required."
        )
    
    db_category = CategoryModel(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    # Clear category caches
    delete_cache("categories:*")
    return db_category

@router.put("/{category_id}", response_model=Category)
async def update_category(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Update a category (admin only).
    """
    # Verify authentication and superuser status
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Superuser required."
        )
    
    db_category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    
    # Clear relevant caches
    delete_cache(f"category:{category_id}")
    delete_cache("categories:*")
    return db_category

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Delete a category (admin only).
    """
    # Verify authentication and superuser status
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Superuser required."
        )
    
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(category)
    db.commit()
    
    # Clear relevant caches
    delete_cache(f"category:{category_id}")
    delete_cache("categories:*")
    return {"message": "Category deleted successfully"}

@router.get("/{category_id}/products", response_model=List[Product])
async def get_category_products(
    category_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Get all products in a specific category.
    """
    # Verify authentication
    current_user = await deps.get_current_user(credentials, db)
    
    cache_key = f"category:{category_id}:products:{skip}:{limit}"
    cached_data = get_cache(cache_key)
    if cached_data:
        return cached_data
    
    products = db.query(ProductModel)\
        .filter(ProductModel.category_id == category_id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    set_cache(cache_key, products, expire=1800)
    return products 