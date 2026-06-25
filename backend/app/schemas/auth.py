from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class VerifyEmailRequest(BaseModel):
    token: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    message: str
    email: EmailStr
    verification_token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerificationResponse(BaseModel):
    message: str