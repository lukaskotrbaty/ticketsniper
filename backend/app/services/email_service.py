import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

from app.core.config import settings
from app.core.security import create_email_confirmation_token

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _send_email_sync(
    email_to: str,
    subject: str = "",
    plain_text_content: str = "",
) -> bool:
    """
    Synchronous function to send email using smtplib.
    This function will be run in a separate thread.
    """
    assert settings.EMAILS_FROM_EMAIL, "EMAILS_FROM_EMAIL must be set"
    assert settings.SMTP_HOST, "SMTP_HOST must be set"
    assert settings.SMTP_USER, "SMTP_USER must be set"
    assert settings.SMTP_PASSWORD, "SMTP_PASSWORD must be set"

    # Create MIMEText object
    # Ensure content is UTF-8 encoded
    msg = MIMEText(plain_text_content, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    # Use formataddr for proper From header formatting
    msg['From'] = formataddr((str(Header('Ticket Sniper', 'utf-8')), settings.EMAILS_FROM_EMAIL))
    msg['To'] = email_to

    try:
        # Choose SMTP_SSL or SMTP (with STARTTLS) based on settings
        if settings.SMTP_SSL:
            logger.debug(f"Connecting to {settings.SMTP_HOST}:{settings.SMTP_PORT} using SMTP_SSL")
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
            # No need for starttls() with SMTP_SSL
        elif settings.SMTP_TLS:
            logger.debug(f"Connecting to {settings.SMTP_HOST}:{settings.SMTP_PORT} using SMTP with STARTTLS")
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
        else:
            # Allow non-secure connection if explicitly configured (not recommended)
            logger.debug(f"Connecting to {settings.SMTP_HOST}:{settings.SMTP_PORT} using plain SMTP")
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)

        # Login and send
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        logger.debug(f"Sending email to {email_to}")
        server.sendmail(settings.EMAILS_FROM_EMAIL, [email_to], msg.as_string())
        server.quit()
        logger.info(f"Email successfully sent to {email_to}")
        return True
    except smtplib.SMTPException as e:
        logger.exception(f"SMTP error occurred while sending email to {email_to}: {e}")
        return False
    except Exception as e:
        logger.exception(f"An unexpected error occurred while sending email to {email_to}: {e}")
        return False

async def send_email(
    email_to: str,
    subject: str = "",
    plain_text_content: str = "",
) -> bool:
    """
    Asynchronously sends an email by running the synchronous smtplib code
    in a separate thread.
    """
    # Run the synchronous sending function in a thread pool
    loop = asyncio.get_running_loop()
    try:
        success = await loop.run_in_executor(
            None,  # Use default executor (ThreadPoolExecutor)
            _send_email_sync,
            email_to,
            subject,
            plain_text_content
        )
        return success
    except Exception as e:
        # Catch potential errors during thread execution scheduling/running
        logger.exception(f"Error scheduling/running email sending task for {email_to}: {e}")
        return False


async def send_password_reset_email(email_to: str, reset_token: str) -> bool:
    """Sends the password reset email to a user."""
    subject = "Žádost o obnovení hesla pro Ticket Sniper"
    # Construct the reset URL using the frontend base URL and the token
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{reset_token}"
    expire_minutes = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES

    # Plain text content based on the proposed template
    plain_text = f"""Dobrý den,

obdrželi jsme žádost o obnovení hesla pro Váš účet spojený s tímto emailem.

Pro nastavení nového hesla klikněte na následující odkaz:
{reset_url}

Tento odkaz je platný po dobu {expire_minutes} minut.

Pokud jste o obnovení hesla nežádali, tento email prosím ignorujte.

S pozdravem,
Tým Ticket Sniper
"""

    return await send_email(
        email_to=email_to,
        subject=subject,
        plain_text_content=plain_text,
    )


async def send_registration_confirmation_email(email_to: str) -> bool:
    """Sends the email confirmation email to a new user."""
    subject = "Potvrďte svůj email pro Ticket Sniper" # Updated subject
    confirmation_token = create_email_confirmation_token(email=email_to)
    confirmation_url = f"{settings.EMAIL_CONFIRMATION_URL_BASE}?token={confirmation_token}"

    # Plain text content
    plain_text = f"""Dobrý den,

děkujeme za registraci do Ticket Sniper.

Pro potvrzení Vaší emailové adresy klikněte (nebo zkopírujte do prohlížeče) následující odkaz:
{confirmation_url}

Pokud jste se neregistrovali, tento email prosím ignorujte.

S pozdravem,
Tým Ticket Sniper
"""

    return await send_email(
        email_to=email_to,
        subject=subject,
        plain_text_content=plain_text,
    )
