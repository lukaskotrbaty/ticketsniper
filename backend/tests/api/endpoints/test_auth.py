from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import crud_user
from app.schemas.user import UserCreate
from app.core import security

pytestmark = pytest.mark.asyncio


class TestAuthEndpoints:
    async def test_register_new_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """
        Test successful registration of a new user.
        """
        with patch(
            "app.services.email_service.send_registration_confirmation_email",
            new_callable=AsyncMock,
        ) as mock_send_email:
            user_data = {
                "email": "test@example.com",
                "password": "testpassword123",
                "password_confirm": "testpassword123",
            }
            response = await client.post("/api/v1/auth/register", json=user_data)

            assert response.status_code == 201, response.text
            # The endpoint returns the user object, not a message
            response_data = response.json()
            assert response_data["email"] == user_data["email"]
            assert "id" in response_data
            assert "is_verified" in response_data and not response_data["is_verified"]

            # Verify email was called with the correct recipient
            mock_send_email.assert_called_once_with(email_to=user_data["email"])

            # Verify user is in the database and not verified
            db_user = await crud_user.get_user_by_email(
                db_session, email=user_data["email"]
            )
            assert db_user is not None
            assert db_user.email == user_data["email"]
            assert not db_user.is_verified

    async def test_login_for_access_token(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """
        Test successful login and token generation for a verified user.
        """
        # 1. Create a verified user in the database first
        password = "testpassword123"
        user_in = UserCreate(
            email="verified@example.com",
            password=password,
            password_confirm=password,
        )
        user = await crud_user.create_user(db=db_session, user_in=user_in)
        user.is_verified = True
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # 2. Attempt to login
        login_data = {"username": user.email, "password": password}
        response = await client.post("/api/v1/auth/login", data=login_data)

        # 3. Verify the response
        assert response.status_code == 200
        token = response.json()
        assert "access_token" in token
        assert token["token_type"] == "bearer"

    async def test_confirm_email(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """
        Test successful email confirmation.
        """
        # 1. Create an unverified user
        password = "testpassword123"
        user_in = UserCreate(
            email="unverified@example.com",
            password=password,
            password_confirm=password,
        )
        user = await crud_user.create_user(db=db_session, user_in=user_in)

        # 2. Generate a confirmation token for the user
        token = security.create_email_confirmation_token(user.email)

        # 3. Make the confirmation request
        response = await client.get(f"/api/v1/auth/confirm/{token}")

        # 4. Verify the response and user status
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["email"] == user.email
        assert response_data["is_verified"] is True

        # 5. Verify the user is updated in the database
        db_user = await crud_user.get_user_by_email(db_session, email=user.email)
        assert db_user is not None
        # The db_user object might be stale, refresh it to get the latest state from the DB
        await db_session.refresh(db_user)
        assert db_user.is_verified is True
