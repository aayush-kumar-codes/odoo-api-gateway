from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class BasketItemBase(BaseModel):
    product_id: int
    quantity: int = 1

class BasketItemCreate(BasketItemBase):
    pass

class BasketItem(BasketItemBase):
    id: int
    price_unit: float
    basket_id: int

    class Config:
        from_attributes = True

class Basket(BaseModel):
    id: int
    user_id: int
    total_price: float
    created_at: datetime
    updated_at: datetime
    items: List[BasketItem]

    class Config:
        from_attributes = True 