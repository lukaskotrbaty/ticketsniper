import smtplib
import pytest
import email
from email.header import decode_header
from unittest.mock import patch, MagicMock, AsyncMock

from app.services import email_service
from app.core.config import settings


@pytest.fixture
def mock_smtp_ssl():
    """Fixture to mock the smtplib.SMTP_SSL class."""
    with patch("smtplib.SMTP_SSL", autospec=True) as mock_smtp_class:
        mock_instance = mock_smtp_class.return_value
        yield mock_smtp_class, mock_instance


@patch("app.services.email_service.send_email", new_callable=AsyncMock)
@patch("app.services.email_service.create_email_confirmation_token", return_value="test_token")
@pytest.mark.asyncio
async def test_send_registration_confirmation_email(mock_create_token, mock_send_email):
    """
    Test that the registration confirmation email is sent with the correct subject and content.
    """
    # Arrange
    email_to = "new.user@example.com"
    
    # Act
    await email_service.send_registration_confirmation_email(email_to)
    
    # Assert
    mock_send_email.assert_awaited_once()
    call_args = mock_send_email.call_args[1]
    
    assert call_args['email_to'] == email_to
    assert "Potvrďte svůj email" in call_args['subject']
    # Check that the generated token is in the email body
    assert "token=test_token" in call_args['plain_text_content']


@patch("app.services.email_service.send_email", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_send_password_reset_email(mock_send_email):
    """
    Test that the password reset email is sent with the correct subject and content.
    """
    # Arrange
    email_to = "user@example.com"
    reset_token = "password_reset_token_123"
    
    # Act
    await email_service.send_password_reset_email(email_to, reset_token)
    
    # Assert
    mock_send_email.assert_awaited_once()
    call_args = mock_send_email.call_args[1]
    
    assert call_args['email_to'] == email_to
    assert "obnovení hesla" in call_args['subject']
    # Check that the reset token is in the email body
    assert f"/{reset_token}" in call_args['plain_text_content']


