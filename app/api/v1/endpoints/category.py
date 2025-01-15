from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.product import Category, CategoryCreate, Product
from app.models.category import Category as CategoryModel
from app.models.product import Product as ProductModel
from app.models.user import User
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, delete_cache

router = APIRouter()

@router.get("/", response_model=List[Category])
async def get_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    vendor_id: Optional[int] = None,
    parent_id: Optional[int] = None
):
    """
    Retrieve categories with optional filtering by vendor and parent.
    """
    query = db.query(CategoryModel)
    
    if vendor_id:
        query = query.filter(CategoryModel.vendor_id == vendor_id)
    if parent_id:
        query = query.filter(CategoryModel.parent_id == parent_id)
    
    categories = query.offset(skip).limit(limit).all()
    return categories

@router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific category by ID.
    """
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
    current_user: User = Depends(deps.get_current_superuser)
):
    """
    Create a new category (admin only).
    """
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
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update a category (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    delete_cache(f"category:{category_id}")
    delete_cache("categories:*")
    return db_category

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete a category (admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(category)
    db.commit()
    delete_cache(f"category:{category_id}")
    delete_cache("categories:*")
    return {"message": "Category deleted successfully"}

@router.get("/{category_id}/products", response_model=List[Product])
async def get_category_products(
    category_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all products in a specific category.
    """
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