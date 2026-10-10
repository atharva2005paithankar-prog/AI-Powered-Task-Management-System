from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Body of POST /api/auth/register. Note: there is no 'role' field,
    so nobody can register themselves as an admin."""

    name: str = Field(min_length=2, max_length=100, examples=["Asha Patil"])
    email: EmailStr = Field(examples=["asha@example.com"])
    password: str = Field(min_length=8, max_length=72, examples=["StrongPass@123"])

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must have at least 2 characters")
        return value

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, value: str) -> str:
        # bcrypt only looks at the first 72 BYTES of a password.
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes long")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    """What we send back about a user. The password hash is never included."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    created_at: datetime
    updated_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
