from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.product import product_category

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    
    # Define relationships
    parent = relationship("Category", remote_side=[id], backref="children")
    vendor = relationship("Vendor", back_populates="categories")
    products = relationship("Product", secondary=product_category,overlaps="categories") 