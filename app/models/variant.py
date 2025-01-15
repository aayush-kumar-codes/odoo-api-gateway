from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class ProductVariant(Base):
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    product_template_id = Column(Integer, ForeignKey("products.id"))
    sku = Column(String, unique=True, index=True)
    price = Column(Float)
    barcode = Column(String)
    price_extra = Column(Float, default=0.0)
    
    product = relationship("Product", back_populates="variants")
    attribute_values = relationship("ProductAttributeValue", back_populates="variant") 