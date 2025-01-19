from typing import Optional
from pydantic import BaseModel, EmailStr, constr

class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    is_active: Optional[bool] = True
    is_company: Optional[bool] = False

class UserCreate(UserBase):
    password: constr(min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_company: Optional[bool] = None

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: constr(min_length=8)

class User(UserBase):
    id: int
    is_superuser: bool = False

    model_config = {
        "from_attributes": True
    } 