from typing import Optional
from pydantic import BaseModel, EmailStr

class VendorBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state_id: Optional[int] = None
    zip: Optional[str] = None
    country_id: Optional[int] = None
    is_company: bool = True
    is_active: bool = True

class VendorCreate(VendorBase):
    pass

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state_id: Optional[int] = None
    zip: Optional[str] = None
    country_id: Optional[int] = None
    is_active: Optional[bool] = None

class Vendor(VendorBase):
    id: int

    class Config:
        from_attributes = True 