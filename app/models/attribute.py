from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base

class ProductAttribute(Base):
    __tablename__ = "product_attributes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    display_type = Column(String, default="radio")
    is_custom = Column(Boolean, default=False)
    sequence = Column(Integer, default=0)
    
    values = relationship("ProductAttributeValue", back_populates="attribute") 