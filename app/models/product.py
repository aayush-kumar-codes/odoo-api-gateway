from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from app.db.session import Base

# Many-to-many relationship table
product_category = Table(
    'product_category',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    list_price = Column(Float)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    is_active = Column(Boolean, default=True)
    image_url = Column(String)
    tags = Column(String)
    barcode = Column(String)
    
    # Change the relationship definition to avoid backref conflict
    categories = relationship("Category", secondary=product_category)
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    vendor = relationship("Vendor", back_populates="products") 