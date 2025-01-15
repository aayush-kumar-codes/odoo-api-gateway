from typing import List, Optional
from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    vendor_id: int

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    children: List["Category"] = []
    vendor_id: int
    
    class Config:
        from_attributes = True 