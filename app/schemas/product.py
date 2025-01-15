from typing import Optional, List
from pydantic import BaseModel

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

class ProductAttributeValue(BaseModel):
    id: int
    name: str
    attribute_id: int
    sequence: int = 0
    is_custom: bool = False
    variant_id: Optional[int] = None

    class Config:
        from_attributes = True

class ProductVariantCreate(BaseModel):
    product_id: int
    sku: str
    price: float
    barcode: Optional[str] = None
    price_extra: Optional[float] = 0.0
    attribute_values: List[ProductAttributeValue]

class ProductVariant(BaseModel):
    id: int
    product_template_id: int
    sku: str
    price: float
    barcode: Optional[str] = None
    price_extra: float = 0.0
    attribute_values: List[ProductAttributeValue]

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    list_price: float
    category_ids: List[int]
    vendor_id: int
    is_active: bool = True
    image_url: Optional[str] = None
    tags: Optional[str] = None
    barcode: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    variants: List[ProductVariant] = []
    
    class Config:
        from_attributes = True 