from pydantic import BaseModel, EmailStr, field_validator
# Import validation function from user schema
from .user import validate_password_strength

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    # Stores data extracted from the JWT token (e.g., user identifier)
    # Uses 'sub' (subject) as per JWT standard convention
    sub: str | None = None

# --- Password Reset Schemas ---

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    # Validator for new password strength
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        # Reuse the same strength validation logic as in registration
        return validate_password_strength(value)
