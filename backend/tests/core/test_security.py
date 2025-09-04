import pytest
from jose import jwt
from datetime import timedelta
from unittest.mock import patch

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    create_email_confirmation_token,
    verify_token,
)
from app.core.config import settings

def test_password_hashing_and_verification():
    """
    Test that a password is correctly hashed and that the hash can be verified.
    """
    password = "plain_password"
    hashed_password = get_password_hash(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrong_password", hashed_password) is False

def test_create_access_token():
    """
    Test that an access token is created with the correct subject and expires correctly.
    """
    subject = "test_subject"
    expires_delta = timedelta(minutes=15)
    
    token = create_access_token(subject, expires_delta)
    
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    
    assert payload["sub"] == subject
    assert "exp" in payload

def test_email_confirmation_token():
    """
    Test the creation and verification of an email confirmation token.
    """
    email = "test@example.com"
    token = create_email_confirmation_token(email)
    
    token_data = verify_token(token, expected_scope="email_confirmation")
    assert token_data is not None
    assert token_data.sub == email

def test_verify_invalid_email_confirmation_token():
    """
    Test that an invalid or tampered token fails verification.
    """
    invalid_token = "this.is.an.invalid.token"
    token_data = verify_token(invalid_token, expected_scope="email_confirmation")
    assert token_data is None

def test_verify_wrong_scope_token():
    """
    Test that a token with a different scope fails verification.
    """
    # Create a standard access token (no scope)
    token = create_access_token("test@example.com")
    token_data = verify_token(token, expected_scope="email_confirmation")
    assert token_data is None

@patch("app.core.security.settings.EMAIL_CONFIRMATION_TOKEN_EXPIRE_MINUTES", -1)
def test_verify_expired_email_confirmation_token():
    """
    Test that an expired token fails verification by mocking the expiration time.
    """
    email = "expired@example.com"
    # Create a token that is already expired due to the mocked setting
    expired_token = create_email_confirmation_token(email)
    
    token_data = verify_token(expired_token, expected_scope="email_confirmation")
    assert token_data is None
