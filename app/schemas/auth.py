from typing import Optional
from pydantic import BaseModel, EmailStr

class OdooLogin(BaseModel):
    login: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    odoo_uid: int

class TokenPayload(BaseModel):
    sub: str | None = None
    refresh: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class RefreshToken(BaseModel):
    refresh_token: str 