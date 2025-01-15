from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Basket(Base):
    __tablename__ = "baskets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_price = Column(Float, default=0.0)
    
    user = relationship("User", back_populates="basket")
    items = relationship("BasketItem", back_populates="basket", cascade="all, delete-orphan")

class BasketItem(Base):
    __tablename__ = "basket_items"
    
    id = Column(Integer, primary_key=True, index=True)
    basket_id = Column(Integer, ForeignKey("baskets.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    price_unit = Column(Float)
    
    basket = relationship("Basket", back_populates="items")
    product = relationship("Product") 