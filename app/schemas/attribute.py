from typing import List, Optional
from pydantic import BaseModel

class AttributeBase(BaseModel):
    name: str
    display_type: str = "radio"
    is_custom: bool = False
    sequence: int = 0
    value_ids: List[int] = []

class AttributeCreate(AttributeBase):
    pass

class Attribute(AttributeBase):
    id: int
    values: List["AttributeValue"] = []
    
    class Config:
        from_attributes = True 