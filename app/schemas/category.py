from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    vendor_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    vendor_id: int

class Category(CategoryBase):
    id: int
    children: List["Category"] = []
    
    model_config = ConfigDict(from_attributes=True)

# This is needed for the recursive List["Category"] reference
Category.model_rebuild() 