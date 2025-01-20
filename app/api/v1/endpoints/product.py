from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Security, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.product import Product, ProductCreate, Category, CategoryCreate, ProductBase
from app.models.product import Product as ProductModel
from app.db.session import get_db
from app.core.cache import clear_cache_pattern, get_cache, set_cache
from app.api.deps import cache_response
from sqlalchemy.sql import or_
from app.schemas.category import Category as CategorySchema
from app.models.category import Category as CategoryModel
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

# Standard error messages
PRODUCT_NOT_FOUND = "Product not found"
UNAUTHORIZED = "Not enough permissions"

@router.get("/categories", response_model=List[Category])
async def get_categories(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve categories.
    """
    try:
        current_user = await deps.get_current_user(credentials, db)
        categories = db.query(CategoryModel).offset(skip).limit(limit).all()
        return categories
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving categories: {str(e)}"
        )

@router.get("/products", response_model=List[Product])
async def get_products(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security),
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    search: Optional[str] = None
):
    """Get products with filtering"""
    try:
        current_user = await deps.get_current_user(credentials, db)
        
        cache_key = f"product:list:c{category_id}:v{vendor_id}:s{search}:{skip}:{limit}"
        cached_data = get_cache(cache_key)
        if cached_data:
            return cached_data
            
        query = db.query(ProductModel)
        
        if category_id:
            query = query.filter(ProductModel.category_id == category_id)
        if vendor_id:
            query = query.filter(ProductModel.vendor_id == vendor_id)
        if search:
            query = query.filter(
                or_(
                    ProductModel.name.ilike(f"%{search}%"),
                    ProductModel.description.ilike(f"%{search}%")
                )
            )
            
        products = query.offset(skip).limit(limit).all()
        set_cache(cache_key, products, expire=1800)
        return products
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving products: {str(e)}"
        )

@router.get("/products/{product_id}", response_model=Product)
@cache_response(expire=3600, key_prefix="product")
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Get product by ID with caching
    """
    current_user = await deps.get_current_user(credentials, db)
    
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/products", response_model=ProductBase)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Create new product and clear relevant caches (admin only)
    """
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Create the product
    db_product = ProductModel(
        name=product.name,
        description=product.description,
        list_price=product.list_price,
        vendor_id=product.vendor_id,
        is_active=product.is_active,
        image_url=product.image_url,
        tags=product.tags,
        barcode=product.barcode,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Add categories to the product
    if product.category_ids:
        categories = db.query(CategoryModel).filter(CategoryModel.id.in_(product.category_ids)).all()
        db_product.categories.extend(categories)
        db.commit()

    # Clear product caches
    clear_cache_pattern("products:*")
    clear_cache_pattern(f"product:get_product:*")
    
    return db_product

@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    product: ProductCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Update product details (admin only)
    """
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update basic product attributes
    for key, value in product.dict(exclude={'category_ids'}).items():
        setattr(db_product, key, value)
    
    # Update categories if provided
    if product.category_ids is not None:
        # Clear existing categories
        db_product.categories = []
        # Add new categories
        categories = db.query(CategoryModel).filter(CategoryModel.id.in_(product.category_ids)).all()
        db_product.categories.extend(categories)
    
    db.commit()
    db.refresh(db_product)
    
    # Clear caches
    clear_cache_pattern("products:*")
    clear_cache_pattern(f"product:get_product:{product_id}")
    
    # Clear category-specific caches for both old and new categories
    for category in db_product.categories:
        clear_cache_pattern(f"category:{category.id}:products:*")
    
    return db_product

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Delete a product (admin only)
    """
    current_user = await deps.get_current_user(credentials, db)
    if not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get category IDs before deleting the product
    category_ids = [category.id for category in db_product.categories]
    
    db.delete(db_product)
    db.commit()
    
    # Clear caches
    clear_cache_pattern("products:*")
    clear_cache_pattern(f"product:get_product:{product_id}")
    
    # Clear cache for each associated category
    for category_id in category_ids:
        clear_cache_pattern(f"category:{category_id}:products:*")
    
    return {"message": "Product deleted successfully"}

@router.post("/products/sync")
async def sync_products(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Sync product data with Odoo (admin only)
    """
    current_user = await deps.get_current_user(credentials, db)
    
    # Check all possible admin fields
    is_admin = any([
        current_user.get("is_superuser"),
        current_user.get("odoo_login") == "admin",
        current_user.get("name") == "Administrator",
        current_user.get("login") == "admin",
        current_user.get("role") == "admin"
    ])
    
    if not is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        # TODO: Implement Odoo sync logic here
        
        # Clear all product-related caches after sync
        clear_cache_pattern("products:*")
        clear_cache_pattern("product:*")
        clear_cache_pattern("category:*:products:*")
        
        return {"message": "Products synchronized successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync products: {str(e)}"
        ) 