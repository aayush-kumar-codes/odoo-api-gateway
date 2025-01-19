from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.basket import Basket, BasketItem, BasketItemCreate
from app.models.basket import Basket as BasketModel, BasketItem as BasketItemModel
from app.models.product import Product
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, delete_cache
from fastapi.security import HTTPAuthorizationCredentials

router = APIRouter()

# Standard error messages
BASKET_NOT_FOUND = "Basket not found"
PRODUCT_NOT_FOUND = "Product not found"
UNAUTHORIZED = "Not enough permissions"

@router.get("/", response_model=Basket)
async def get_basket(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Get current user's basket"""
    try:
        current_user = await deps.get_current_user(credentials, db)
        user_id = current_user.get('id')
        
        cache_key = f"basket:detail:{user_id}"
        cached_data = get_cache(cache_key)
        if cached_data:
            return cached_data
        
        basket = db.query(BasketModel).filter(BasketModel.user_id == user_id).first()
        if not basket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=BASKET_NOT_FOUND
            )
        
        set_cache(cache_key, basket, expire=3600)
        return basket
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving basket: {str(e)}"
        )

@router.post("/", response_model=Basket)
async def create_basket(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """Create a new basket for current user"""
    try:
        current_user = await deps.get_current_user(credentials, db)
        user_id = current_user.get('id')
        
        existing_basket = db.query(BasketModel).filter(
            BasketModel.user_id == user_id
        ).first()
        
        if existing_basket:
            return existing_basket
        
        basket = BasketModel(user_id=user_id)
        db.add(basket)
        db.commit()
        db.refresh(basket)
        
        # Clear user's basket cache
        delete_cache(f"basket:detail:{user_id}")
        delete_cache(f"basket:items:{user_id}")
        
        return basket
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating basket: {str(e)}"
        )

@router.post("/items", response_model=BasketItem)
async def add_basket_item(
    item: BasketItemCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Add item to basket
    """
    current_user = await deps.get_current_user(credentials, db)
    
    basket = db.query(BasketModel).filter(BasketModel.user_id == current_user.get('id')).first()
    if not basket:
        basket = BasketModel(user_id=current_user.get('id'))
        db.add(basket)
        db.commit()
    
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    basket_item = BasketItemModel(
        basket_id=basket.id,
        product_id=item.product_id,
        quantity=item.quantity,
        price_unit=product.list_price
    )
    
    db.add(basket_item)
    db.commit()
    db.refresh(basket_item)
    
    # Update basket total
    basket.total_price = sum(item.price_unit * item.quantity for item in basket.items)
    db.commit()
    
    # Clear cache
    delete_cache(f"basket:{current_user.get('id')}")
    return basket_item

@router.put("/items/{item_id}", response_model=BasketItem)
async def update_basket_item(
    item_id: int,
    quantity: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Update basket item quantity
    """
    current_user = await deps.get_current_user(credentials, db)
    
    basket = db.query(BasketModel).filter(BasketModel.user_id == current_user.get('id')).first()
    if not basket:
        raise HTTPException(status_code=404, detail="Basket not found")
    
    basket_item = db.query(BasketItemModel).filter(
        BasketItemModel.id == item_id,
        BasketItemModel.basket_id == basket.id
    ).first()
    
    if not basket_item:
        raise HTTPException(status_code=404, detail="Basket item not found")
    
    basket_item.quantity = quantity
    db.commit()
    db.refresh(basket_item)
    
    # Update basket total
    basket.total_price = sum(item.price_unit * item.quantity for item in basket.items)
    db.commit()
    
    # Clear cache
    delete_cache(f"basket:{current_user.get('id')}")
    return basket_item

@router.delete("/items/{item_id}")
async def remove_basket_item(
    item_id: int,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Remove item from basket
    """
    current_user = await deps.get_current_user(credentials, db)
    
    basket = db.query(BasketModel).filter(BasketModel.user_id == current_user.get('id')).first()
    if not basket:
        raise HTTPException(status_code=404, detail="Basket not found")
    
    basket_item = db.query(BasketItemModel).filter(
        BasketItemModel.id == item_id,
        BasketItemModel.basket_id == basket.id
    ).first()
    
    if not basket_item:
        raise HTTPException(status_code=404, detail="Basket item not found")
    
    db.delete(basket_item)
    db.commit()
    
    # Update basket total
    basket.total_price = sum(item.price_unit * item.quantity for item in basket.items)
    db.commit()
    
    # Clear cache
    delete_cache(f"basket:{current_user.get('id')}")
    return {"message": "Item removed from basket"}

@router.post("/clear")
async def clear_basket(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Security(deps.security)
):
    """
    Clear all items from basket
    """
    current_user = await deps.get_current_user(credentials, db)
    
    basket = db.query(BasketModel).filter(BasketModel.user_id == current_user.get('id')).first()
    if not basket:
        raise HTTPException(status_code=404, detail="Basket not found")
    
    for item in basket.items:
        db.delete(item)
    
    basket.total_price = 0
    db.commit()
    
    # Clear cache
    delete_cache(f"basket:{current_user.get('id')}")
    return {"message": "Basket cleared successfully"} 