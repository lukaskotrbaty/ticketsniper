import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db import crud, models
from app.db.session import get_db
from app.schemas import user as user_schema
from app.schemas import token as token_schema
from app.core import security
from app.services import email_service

from app.api.deps import get_current_active_user, get_redis_client
import redis.asyncio as redis
from app.schemas.message import MessageResponse

# Configure logging (Consider moving to a central logging config)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=user_schema.User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: user_schema.UserCreate, db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Register a new user.
    Creates a user with is_verified=False and sends a confirmation email.
    Validates password strength and confirmation.
    """
    existing_user = await crud.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this email already exists.",
        )
    try:
        # Password strength and match are validated by Pydantic model (UserCreate)
        user = await crud.create_user(db=db, user_in=user_in)
    except IntegrityError: # Safeguard against race conditions
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this email already exists.",
        )

    email_sent = await email_service.send_registration_confirmation_email(email_to=user.email)
    if not email_sent:
        # Log the error, but don't fail the registration (important for user experience)
        logger.error(f"Failed to send confirmation email to {user.email}")

    return user


@router.get("/confirm/{token}", response_model=user_schema.User)
async def confirm_email(token: str, db: AsyncSession = Depends(get_db)) -> Any:
    """
    Confirm user email address using the token sent via email.
    """
    token_data = security.verify_token(token, expected_scope="email_confirmation")
    if not token_data or not token_data.sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation token.",
        )

    user = await crud.get_user_by_email(db, email=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    if user.is_verified:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified.",
        )

    activated_user = await crud.activate_user(db=db, db_user=user)
    return activated_user


@router.post("/login", response_model=token_schema.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Uses email as the username field.
    """
    user = await crud.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please check your inbox for the confirmation link.",
        )

    access_token = security.create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=user_schema.User)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    """
    Get current logged-in and active user.
    """
    return current_user


@router.post("/request-password-reset", response_model=MessageResponse)
async def request_password_reset(
    reset_request: token_schema.PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
) -> Any:
    """
    Handles password reset request.
    Generates a reset token and sends it via email ONLY if the user exists and is verified.
    Always returns a generic success message for security reasons (prevents email enumeration).
    """
    logger.info(f"Password reset requested for email: {reset_request.email}")
    user = await crud.get_user_by_email(db, email=reset_request.email)

    # Security: Do not reveal if the email exists or is verified.
    # Send email ONLY if user exists AND is verified.
    if user and user.is_verified:
        try:
            reset_token = await security.create_password_reset_token(redis_client, user_id=user.id)
            email_sent = await email_service.send_password_reset_email(
                email_to=user.email, reset_token=reset_token
            )
            if not email_sent:
                logger.error(f"Failed to send password reset email to {user.email}")
                # Do not return error to the user to prevent probing the email service.
        except Exception as e:
             # Log any other unexpected errors during token creation or email sending
            logger.exception(f"Error during password reset request processing for {reset_request.email}: {e}")


    # Always return a generic message
    return MessageResponse(message="If your email is registered and verified, you will receive a password reset link.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: token_schema.PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
) -> Any:
    """
    Resets the user's password using a valid reset token.
    Validates the new password strength.
    """
    # 1. Validate token and get user ID
    user_id = await security.validate_password_reset_token(redis_client, token=reset_data.token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        )

    # 2. Retrieve user
    user = await crud.get_user_by_id(db, user_id=user_id) # Assumes crud.get_user_by_id exists
    if not user:
        # Should not happen if token was valid, but for robustness:
        await security.invalidate_password_reset_token(redis_client, token=reset_data.token) # Invalidate potentially compromised token
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token - user not found.",
        )

    # 3. Validate new password strength (done by Pydantic model PasswordResetConfirm)
    # Hashed password is created below

    # 4. Hash and update password in DB
    hashed_password = security.get_password_hash(reset_data.new_password)
    # Assumes crud.update_user_password exists:
    updated_user = await crud.update_user_password(db, db_user=user, new_hashed_password=hashed_password)

    # 5. Invalidate the used reset token
    await security.invalidate_password_reset_token(redis_client, token=reset_data.token)

    logger.info(f"Password successfully reset for user ID: {user_id}")
    return MessageResponse(message="Your password has been successfully reset.")
