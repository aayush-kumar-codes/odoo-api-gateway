from typing import Optional
from pydantic import BaseModel

class AttributeValueBase(BaseModel):
    value: str
    display_value: str
    attribute_id: int

class AttributeValueCreate(AttributeValueBase):
    pass

class AttributeValue(AttributeValueBase):
    id: int
    
    class Config:
        from_attributes = True 