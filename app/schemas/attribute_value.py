from pydantic import BaseModel

class AttributeValueBase(BaseModel):
    name: str
    sequence: int = 0
    is_custom: bool = False

class AttributeValueCreate(AttributeValueBase):
    pass

class AttributeValue(AttributeValueBase):
    id: int
    attribute_id: int
    
    class Config:
        from_attributes = True 