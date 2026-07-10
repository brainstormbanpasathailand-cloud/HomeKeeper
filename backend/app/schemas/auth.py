"""Authentication request/response schemas."""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class OAuthStartResponse(BaseModel):
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str
    code_verifier: Optional[str] = None


class OnboardingRequest(BaseModel):
    display_name: Optional[str] = None
    phone: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    subdistrict: Optional[str] = None
    language: Optional[str] = Field(default=None, pattern="^(th|zh|en|ru)$")
    accept_tos: bool = False
    accept_privacy: bool = False


class UserOut(BaseModel):
    id: int
    email: Optional[str]
    phone: Optional[str]
    full_name: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    role: str
    language: str
    onboarding_completed: bool
    email_verified: bool
    phone_verified: bool

    model_config = {"from_attributes": True}


class IdentityOut(BaseModel):
    id: int
    provider: str
    provider_email: Optional[str]
    provider_display_name: Optional[str]

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    id: int
    user_agent: Optional[str]
    ip_address: Optional[str]
    last_used_at: Optional[object] = None
    revoked: bool

    model_config = {"from_attributes": True}
