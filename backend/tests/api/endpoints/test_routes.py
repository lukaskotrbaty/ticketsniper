from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock, ANY

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.crud import crud_route, crud_user
from app.schemas.user import UserCreate
from app.core.security import create_access_token
from app.schemas.route import RouteMonitorRequest
from app.main import app
from app.api import deps

pytestmark = pytest.mark.asyncio


class TestRoutesEndpoints:
    @patch("app.api.endpoints.routes.check_route_availability", new_callable=AsyncMock)
    async def test_monitor_new_route_success(
        self, mock_check_availability: AsyncMock, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """
        Test successfully adding a new route to monitor for an authenticated user.
        This test mocks the dependency `get_current_active_user` to avoid lazy loading issues.
        """
        # 1. Create a user and an auth token
        password = "testpassword123"
        user_email = "test-routes@example.com"
        user_in = UserCreate(
            email=user_email, password=password, password_confirm=password
        )
        user = await crud_user.create_user(db=db_session, user_in=user_in)
        user.is_verified = True
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        access_token = create_access_token(subject=user.email)
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Mock dependencies
        mock_check_availability.return_value = (False, {})
        
        # This is the key to solving the MissingGreenlet error without touching app logic
        app.dependency_overrides[deps.get_current_active_user] = lambda: user

        # 3. Prepare request data
        route_data = RouteMonitorRequest(
            regiojet_route_id="123456789",
            from_location_id="10202002",
            from_location_type="CITY",
            to_location_id="10202003",
            to_location_type="CITY",
            departure_datetime=datetime.now(timezone.utc),
        )

        # 4. Make the request
        response = await client.post(
            "/api/v1/routes/monitor",
            json=route_data.model_dump(mode="json"),
            headers=headers,
        )

        # 5. Assert the response
        assert response.status_code == 201, response.text
        response_json = response.json()
        assert response_json["message"] == "Sledování bylo úspěšně spuštěno."
        assert response_json["available"] is False

        # 6. Verify data in the database
        db_user = await crud_user.get_user_by_email(db_session, email=user_email)
        assert db_user is not None
        
        subscriptions = await crud_route.get_user_subscriptions(db_session, user_id=db_user.id)
        assert len(subscriptions) == 1
        
        monitored_route = await crud_route.get_monitored_route_by_id(db_session, route_id=subscriptions[0].route_id)
        assert monitored_route is not None
        assert monitored_route.regiojet_route_id == route_data.regiojet_route_id
        
        # Clean up the dependency override
        app.dependency_overrides.clear()

    @patch("app.api.endpoints.routes.crud_route.create_user_subscription", new_callable=AsyncMock)
    @patch("app.api.endpoints.routes.crud_route.get_or_create_monitored_route", new_callable=AsyncMock)
    @patch("app.api.endpoints.routes.check_route_availability", new_callable=AsyncMock)
    async def test_monitor_route_tickets_available(
        self,
        mock_check_availability: AsyncMock,
        mock_get_or_create: AsyncMock,
        mock_create_subscription: AsyncMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """
        Test that if tickets are available, the system returns a 200 OK response
        and does not create any monitoring records.
        """
        # 1. Setup user and auth
        password = "testpassword123"
        user_email = "test-available@example.com"
        user_in = UserCreate(email=user_email, password=password, password_confirm=password)
        user = await crud_user.create_user(db=db_session, user_in=user_in)
        user.is_verified = True
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        access_token = create_access_token(subject=user.email)
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Mock dependencies
        mock_check_availability.return_value = (True, {"some_data": "value"})
        app.dependency_overrides[deps.get_current_active_user] = lambda: user

        # 3. Prepare request data
        route_data = RouteMonitorRequest(
            regiojet_route_id="987654321",
            from_location_id="10202002",
            from_location_type="CITY",
            to_location_id="10202003",
            to_location_type="CITY",
            departure_datetime=datetime.now(timezone.utc),
        )

        # 4. Make the request
        response = await client.post(
            "/api/v1/routes/monitor",
            json=route_data.model_dump(mode="json"),
            headers=headers,
        )

        # 5. Assert the response
        assert response.status_code == 200, response.text
        response_json = response.json()
        assert response_json["message"] == "Jízdenky jsou pro tuto trasu aktuálně dostupné. Sledování nebylo spuštěno."
        assert response_json["available"] is True
        assert response_json["details"] == {"some_data": "value"}

        # 6. Verify that no DB operations were made
        mock_get_or_create.assert_not_called()
        mock_create_subscription.assert_not_called()

        # Clean up
        app.dependency_overrides.clear()

    @patch("app.api.endpoints.routes.crud_route.delete_monitored_route", new_callable=AsyncMock)
    @patch("app.api.endpoints.routes.crud_route.count_subscriptions_for_route", new_callable=AsyncMock)
    @patch("app.api.endpoints.routes.crud_route.delete_user_subscription", new_callable=AsyncMock)
    async def test_cancel_monitoring_when_last_subscriber_succeeds_and_deletes_route(
        self,
        mock_delete_subscription: AsyncMock,
        mock_count_subscriptions: AsyncMock,
        mock_delete_route: AsyncMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """
        Test cancelling a subscription when the user is the last subscriber.
        Expects the subscription and the monitored route to be deleted.
        """
        # 1. Setup user, route, and subscription
        user = await crud_user.create_user(db_session, user_in=UserCreate(email="last@example.com", password="password123", password_confirm="password123"))
        user.is_verified = True
        await db_session.commit()

        route_in = RouteMonitorRequest(regiojet_route_id="last_sub_route", from_location_id="1", to_location_id="2", from_location_type="CITY", to_location_type="CITY", departure_datetime=datetime.now(timezone.utc))
        db_route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=route_in)
        await db_session.commit()

        await db_session.refresh(user)
        await db_session.refresh(db_route)
        await crud_route.create_user_subscription(db=db_session, user_id=user.id, route_id=db_route.id)
        await db_session.commit()

        await db_session.refresh(user)
        await db_session.refresh(db_route)
        
        app.dependency_overrides[deps.get_current_active_user] = lambda: user
        access_token = create_access_token(subject=user.email)
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Mock CRUD responses
        mock_delete_subscription.return_value = True
        mock_count_subscriptions.return_value = 0

        # 3. Make the request
        response = await client.delete(f"/api/v1/routes/monitor/{db_route.id}", headers=headers)

        # 4. Assertions
        assert response.status_code == 204
        mock_delete_subscription.assert_called_once_with(db=ANY, user_id=user.id, route_id=db_route.id)
        mock_count_subscriptions.assert_called_once_with(db=ANY, route_id=db_route.id)
        mock_delete_route.assert_called_once_with(db=ANY, route_id=db_route.id)

        # 5. Cleanup
        app.dependency_overrides.clear()

    @patch("app.api.endpoints.routes.crud_route.delete_monitored_route", new_callable=AsyncMock)
    @patch("app.api.endpoints.routes.crud_route.count_subscriptions_for_route", new_callable=AsyncMock)
    @patch("app.api.endpoints.routes.crud_route.delete_user_subscription", new_callable=AsyncMock)
    async def test_cancel_monitoring_when_not_last_subscriber_succeeds_and_keeps_route(
        self,
        mock_delete_subscription: AsyncMock,
        mock_count_subscriptions: AsyncMock,
        mock_delete_route: AsyncMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """
        Test cancelling a subscription when other subscribers still exist.
        Expects only the subscription to be deleted, not the route.
        """
        # 1. Setup
        user = await crud_user.create_user(db_session, user_in=UserCreate(email="notlast@example.com", password="password123", password_confirm="password123"))
        user.is_verified = True
        await db_session.commit()

        route_in = RouteMonitorRequest(regiojet_route_id="not_last_sub_route", from_location_id="1", to_location_id="2", from_location_type="CITY", to_location_type="CITY", departure_datetime=datetime.now(timezone.utc))
        db_route = await crud_route.get_or_create_monitored_route(db=db_session, route_in=route_in)
        await db_session.commit()

        await db_session.refresh(user)
        await db_session.refresh(db_route)
        await crud_route.create_user_subscription(db=db_session, user_id=user.id, route_id=db_route.id)
        await db_session.commit()

        await db_session.refresh(user)
        await db_session.refresh(db_route)

        app.dependency_overrides[deps.get_current_active_user] = lambda: user
        access_token = create_access_token(subject=user.email)
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Mock CRUD responses
        mock_delete_subscription.return_value = True
        mock_count_subscriptions.return_value = 1  # Other subscribers exist

        # 3. Make the request
        response = await client.delete(f"/api/v1/routes/monitor/{db_route.id}", headers=headers)

        # 4. Assertions
        assert response.status_code == 204
        mock_delete_subscription.assert_called_once_with(db=ANY, user_id=user.id, route_id=db_route.id)
        mock_count_subscriptions.assert_called_once_with(db=ANY, route_id=db_route.id)
        mock_delete_route.assert_not_called()

        # 5. Cleanup
        app.dependency_overrides.clear()

    @patch("app.api.endpoints.routes.crud_route.delete_user_subscription", new_callable=AsyncMock)
    async def test_cancel_non_existent_subscription_returns_404(
        self,
        mock_delete_subscription: AsyncMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """
        Test attempting to cancel a subscription that does not exist for the user.
        Expects a 404 Not Found error.
        """
        # 1. Setup
        user = await crud_user.create_user(db_session, user_in=UserCreate(email="no_sub@example.com", password="password123", password_confirm="password123"))
        user.is_verified = True
        await db_session.commit()
        await db_session.refresh(user)

        app.dependency_overrides[deps.get_current_active_user] = lambda: user
        access_token = create_access_token(subject=user.email)
        headers = {"Authorization": f"Bearer {access_token}"}
        
        non_existent_route_id = 999

        # 2. Mock CRUD response
        mock_delete_subscription.return_value = False

        # 3. Make the request
        response = await client.delete(f"/api/v1/routes/monitor/{non_existent_route_id}", headers=headers)

        # 4. Assertions
        assert response.status_code == 404
        assert response.json()["detail"] == "Sledování pro tohoto uživatele a trasu nebylo nalezeno."
        mock_delete_subscription.assert_called_once_with(db=ANY, user_id=user.id, route_id=non_existent_route_id)

        # 5. Cleanup
        app.dependency_overrides.clear()

    @patch("app.api.endpoints.routes.check_route_availability", new_callable=AsyncMock)
    async def test_monitor_route_checker_fails(
        self, mock_check_availability: AsyncMock, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """
        Test that if the availability checker raises an HTTPException,
        it is propagated correctly by the endpoint.
        """
        # 1. Setup user and auth
        password = "testpassword123"
        user_email = "test-fail@example.com"
        user_in = UserCreate(email=user_email, password=password, password_confirm=password)
        user = await crud_user.create_user(db=db_session, user_in=user_in)
        user.is_verified = True
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        access_token = create_access_token(subject=user.email)
        headers = {"Authorization": f"Bearer {access_token}"}

        # 2. Mock dependencies to raise an exception
        mock_check_availability.side_effect = HTTPException(
            status_code=503, detail="Service Unavailable"
        )
        app.dependency_overrides[deps.get_current_active_user] = lambda: user

        # 3. Prepare request data
        route_data = RouteMonitorRequest(
            regiojet_route_id="111222333",
            from_location_id="10202002",
            from_location_type="CITY",
            to_location_id="10202003",
            to_location_type="CITY",
            departure_datetime=datetime.now(timezone.utc),
        )

        # 4. Make the request
        response = await client.post(
            "/api/v1/routes/monitor",
            json=route_data.model_dump(mode="json"),
            headers=headers,
        )

        # 5. Assert the response
        assert response.status_code == 503
        assert response.json()["detail"] == "Service Unavailable"

        # Clean up
        app.dependency_overrides.clear()
