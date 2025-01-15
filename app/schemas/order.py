from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderLineBase(BaseModel):
    product_id: int
    product_uom_qty: float = 1.0
    price_unit: float

class OrderLineCreate(OrderLineBase):
    pass

class OrderLine(OrderLineBase):
    id: int
    order_id: int
    subtotal: float

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    shipping_address: str
    payment_method: Optional[str] = None

class OrderCreate(OrderBase):
    lines: List[OrderLineCreate]

class Order(OrderBase):
    id: int
    name: str
    user_id: int
    state: OrderStatus
    order_date: datetime
    total_price: float
    lines: List[OrderLine]

    class Config:
        from_attributes = True 