from typing import List, Optional
from pydantic import BaseModel

class AttributeBase(BaseModel):
    name: str
    display_name: str
    attribute_type: str
    description: Optional[str] = None

class AttributeCreate(AttributeBase):
    pass

class Attribute(AttributeBase):
    id: int
    
    class Config:
        from_attributes = True 