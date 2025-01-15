from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.basket import Basket, BasketItem, BasketItemCreate
from app.models.basket import Basket as BasketModel, BasketItem as BasketItemModel
from app.models.product import Product
from app.models.user import User
from app.db.session import get_db
from app.core.cache import get_cache, set_cache, delete_cache

router = APIRouter()

@router.get("/", response_model=Basket)
async def get_basket(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get current user's basket
    """
    basket = db.query(BasketModel).filter(BasketModel.user_id == current_user.id).first()
    if not basket:
        raise HTTPException(status_code=404, detail="Basket not found")
    return basket

@router.post("/", response_model=Basket)
async def create_basket(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new basket for current user
    """
    existing_basket = db.query(BasketModel).filter(BasketModel.user_id == current_user.id).first()
    if existing_basket:
        return existing_basket
    
    basket = BasketModel(user_id=current_user.id)
    db.add(basket)
    db.commit()
    db.refresh(basket)
    return basket

@router.post("/items", response_model=BasketItem)
async def add_basket_item(
    item: BasketItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Add item to basket
    """
    basket = db.query(BasketModel).filter(BasketModel.user_id == current_user.id).first()
    if not basket:
        basket = BasketModel(user_id=current_user.id)
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
    
    return basket_item

@router.put("/items/{item_id}", response_model=BasketItem)
async def update_basket_item(
    item_id: int,
    quantity: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update basket item quantity
    """
    basket = db.query(BasketModel).filter(BasketModel.user_id == current_user.id).first()
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
    
    return basket_item

@router.delete("/items/{item_id}")
async def remove_basket_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Remove item from basket
    """
    basket = db.query(BasketModel).filter(BasketModel.user_id == current_user.id).first()
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
    
    return {"message": "Item removed from basket"}

@router.post("/clear")
async def clear_basket(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Clear all items from basket
    """
    basket = db.query(BasketModel).filter(BasketModel.user_id == current_user.id).first()
    if not basket:
        raise HTTPException(status_code=404, detail="Basket not found")
    
    for item in basket.items:
        db.delete(item)
    
    basket.total_price = 0
    db.commit()
    
    return {"message": "Basket cleared successfully"} 