from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str | None = None
    refresh: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class RefreshToken(BaseModel):
    refresh_token: str 