from pydantic import BaseModel, EmailStr, field_validator, model_validator
from datetime import datetime
import re

def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Heslo musí mít alespoň 8 znaků.")
    if not re.search(r"[a-zA-Z]", password):
        raise ValueError("Heslo musí obsahovat alespoň jedno písmeno.")
    if not re.search(r"\d", password):
        raise ValueError("Heslo musí obsahovat alespoň jednu číslici.")
    return password

# Schema for creating a new user (input for /register)
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    password_confirm: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'UserCreate':
        pw1 = self.password
        pw2 = self.password_confirm
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError("Zadaná hesla se neshodují.")
        return self

# Base schema for user data (common fields)
class UserBase(BaseModel):
    email: EmailStr
    is_verified: bool = False

# Schema for reading user data (output from API, e.g., /me)
# Inherits from UserBase and adds fields read from the DB model
class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    # confirmation_token: str | None = None # Removed testing workaround

    # Pydantic V2 config to allow ORM mode (reading data from SQLAlchemy models)
    model_config = {
        "from_attributes": True
    }
