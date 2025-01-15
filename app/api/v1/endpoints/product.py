from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.product import Product, ProductCreate, Category, CategoryCreate
from app.models.product import Product as ProductModel
from app.models.user import User
from app.db.session import get_db
from app.core.cache import clear_cache_pattern
from app.api.deps import cache_response
from sqlalchemy.sql import or_

router = APIRouter()

@router.get("/categories", response_model=List[Category])
def get_categories(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve categories.
    """
    return db.query(Category).offset(skip).limit(limit).all()

@router.get("/products", response_model=List[Product])
@cache_response(expire=1800, key_prefix="products")
async def get_products(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    tags: Optional[str] = None,
    has_variants: Optional[bool] = None,
    sort_by: Optional[str] = Query(None, enum=["price_asc", "price_desc", "name_asc", "name_desc"]),
):
    """
    Retrieve products with enhanced filtering
    """
    query = db.query(ProductModel)
    
    # Apply filters
    if category_id:
        query = query.filter(ProductModel.category_id == category_id)
    if vendor_id:
        query = query.filter(ProductModel.vendor_id == vendor_id)
    if search:
        query = query.filter(
            or_(
                ProductModel.name.ilike(f"%{search}%"),
                ProductModel.description.ilike(f"%{search}%"),
                ProductModel.tags.ilike(f"%{search}%")
            )
        )
    if tags:
        query = query.filter(ProductModel.tags.ilike(f"%{tags}%"))
    if min_price:
        query = query.filter(ProductModel.list_price >= min_price)
    if max_price:
        query = query.filter(ProductModel.list_price <= max_price)
    if has_variants is not None:
        query = query.filter(ProductModel.variants.any() if has_variants else ~ProductModel.variants.any())
    
    # Apply sorting
    if sort_by:
        if sort_by == "price_asc":
            query = query.order_by(ProductModel.list_price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(ProductModel.list_price.desc())
        elif sort_by == "name_asc":
            query = query.order_by(ProductModel.name.asc())
        elif sort_by == "name_desc":
            query = query.order_by(ProductModel.name.desc())
    
    return query.offset(skip).limit(limit).all()

@router.get("/products/{product_id}", response_model=Product)
@cache_response(expire=3600, key_prefix="product")  # Cache for 1 hour
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get product by ID with caching
    """
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/products", response_model=Product)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create new product and clear relevant caches
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_product = ProductModel(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Clear product caches
    clear_cache_pattern("products:*")
    clear_cache_pattern(f"product:get_product:*")
    
    return db_product 

@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update product details (admin only)
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    
    # Clear caches
    clear_cache_pattern("products:*")
    clear_cache_pattern(f"product:get_product:{product_id}")
    clear_cache_pattern(f"category:{db_product.category_id}:products:*")
    
    return db_product

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete a product (admin only)
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    category_id = db_product.category_id
    db.delete(db_product)
    db.commit()
    
    # Clear caches
    clear_cache_pattern("products:*")
    clear_cache_pattern(f"product:get_product:{product_id}")
    clear_cache_pattern(f"category:{category_id}:products:*")
    
    return {"message": "Product deleted successfully"}

@router.post("/products/sync")
async def sync_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Sync product data with Odoo (admin only)
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        # TODO: Implement Odoo sync logic here
        # This would involve:
        # 1. Connecting to Odoo using XML-RPC
        # 2. Fetching updated product data
        # 3. Updating local database
        
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