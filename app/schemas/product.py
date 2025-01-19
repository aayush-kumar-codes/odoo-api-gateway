from typing import List, Optional
from pydantic import BaseModel
from .attribute import Attribute
from .attribute_value import AttributeValue

class ProductAttributeValue(BaseModel):
    id: int
    attribute_id: int
    value: str
    display_value: str
    
    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    
    class Config:
        from_attributes = True

class ProductVariantBase(BaseModel):
    sku: str
    price: float
    stock_quantity: int
    attribute_values: List[ProductAttributeValue] = []

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariant(ProductVariantBase):
    id: int
    product_id: int
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    list_price: float
    vendor_id: int
    is_active: bool = True
    image_url: Optional[str] = None
    tags: Optional[str] = None
    barcode: Optional[str] = None
   

    class Config:
        model_config = {
            "from_attributes": True
        }

class ProductCreate(ProductBase):
    category_ids: List[int]
   

class Product(ProductBase):
    id: int
    variants: List[ProductVariant] = []
    
    class Config:
        from_attributes = True 