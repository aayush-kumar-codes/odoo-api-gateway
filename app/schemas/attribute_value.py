from typing import Optional
from pydantic import BaseModel

class AttributeValueBase(BaseModel):
    value: str
    display_value: str
    sequence: int = 0
    is_custom: bool = False
    variant_id: Optional[int] = None

class AttributeValueCreate(AttributeValueBase):
    pass

class AttributeValue(AttributeValueBase):
    id: int
    name: str
    attribute_id: int
    
    class Config:
        from_attributes = True