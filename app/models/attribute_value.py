from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class ProductAttributeValue(Base):
    __tablename__ = "product_attribute_values"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    attribute_id = Column(Integer, ForeignKey("product_attributes.id"))
    sequence = Column(Integer, default=0)
    is_custom = Column(Boolean, default=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"))
    variant = relationship("ProductVariant", back_populates="attribute_values")
    
    attribute = relationship("ProductAttribute", back_populates="values") 