from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base

class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    state = Column(Enum(OrderStatus), default=OrderStatus.DRAFT)
    order_date = Column(DateTime, default=datetime.utcnow)
    total_price = Column(Float, default=0.0)
    shipping_address = Column(String)
    payment_method = Column(String)
    
    user = relationship("User", back_populates="orders")
    lines = relationship("OrderLine", back_populates="order", cascade="all, delete-orphan")

class OrderLine(Base):
    __tablename__ = "order_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    product_uom_qty = Column(Float, default=1.0)
    price_unit = Column(Float)
    subtotal = Column(Float)
    
    order = relationship("Order", back_populates="lines")
    product = relationship("Product") 