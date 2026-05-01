from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class AuthIdentityRequest(BaseModel):
    email: EmailStr


class AuthIdentityResponse(BaseModel):
    status: Literal["existing", "new"]

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class OTPRequest(BaseModel):
    email: EmailStr
    purpose: Literal["register", "reset_password"]


class RegisterVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    password: str = Field(min_length=6, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"

class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class GoogleLoginRequest(BaseModel):
    id_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=6, max_length=128)

class VerifyEmailRequest(BaseModel):
    token: str
