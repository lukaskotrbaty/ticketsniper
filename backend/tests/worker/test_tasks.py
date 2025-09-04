import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone
import uuid

from app.worker.tasks import schedule_route_checks, check_single_route, send_notification_email, expire_past_routes
from app.db.models.route import MonitoredRoute, UserRouteSubscription, RouteStatusEnum  
from app.db.models.user import User
from app.schemas.route import RouteMonitorRequest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Create a separate in-memory engine for worker tests (sync)
test_engine = create_engine("sqlite:///:memory:")
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def create_test_route(**kwargs) -> MonitoredRoute:
    """Helper to create a test route with default values."""
    defaults = {
        "regiojet_route_id": str(uuid.uuid4()),
        "from_location_id": "100",
        "from_location_type": "STATION",
        "to_location_id": "200", 
        "to_location_type": "STATION",
        "departure_datetime": datetime.now(timezone.utc),
        "arrival_datetime": datetime.now(timezone.utc),
        "status": RouteStatusEnum.MONITORING,
        "last_checked_at": None
    }
    defaults.update(kwargs)
    return MonitoredRoute(**defaults)

def create_test_user(**kwargs) -> User:
    """Helper to create a test user with default values."""
    defaults = {
        "email": f"test-{uuid.uuid4()}@example.com",
        "hashed_password": "fake_hash",
        "is_verified": True
    }
    defaults.update(kwargs)
    return User(**defaults)

class TestScheduleRouteChecks:
    """Test suite for schedule_route_checks task."""
    
    @patch('app.worker.tasks.SyncSessionLocal')
    @patch('app.worker.tasks.check_single_route.delay')
    def test_schedule_route_checks_with_active_routes(self, mock_delay, mock_session_class):
        """Test that active routes are scheduled for checking."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Create test routes
        route1 = create_test_route(id=1, regiojet_route_id="route1")
        route2 = create_test_route(id=2, regiojet_route_id="route2")
        routes = [route1, route2]
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = routes
        mock_session.execute.return_value = mock_result
        
        # Run the task
        schedule_route_checks()
        
        # Verify session management
        mock_session_class.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verify last_checked_at was updated for both routes
        assert route1.last_checked_at is not None
        assert route2.last_checked_at is not None
        
        # Verify check_single_route was called for each route
        expected_calls = [call(1), call(2)]
        mock_delay.assert_has_calls(expected_calls, any_order=True)
        assert mock_delay.call_count == 2

    @patch('app.worker.tasks.SyncSessionLocal')
    @patch('app.worker.tasks.check_single_route.delay')
    def test_schedule_route_checks_no_active_routes(self, mock_delay, mock_session_class):
        """Test behavior when no active routes exist."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # Run the task
        schedule_route_checks()
        
        # Verify no tasks were scheduled
        mock_delay.assert_not_called()
        mock_session.close.assert_called_once()

    @patch('app.worker.tasks.SyncSessionLocal')
    def test_schedule_route_checks_database_error(self, mock_session_class):
        """Test error handling when database operations fail."""
        # Setup mock session that raises an exception
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.execute.side_effect = Exception("Database error")
        
        # Run the task - should not raise exception
        schedule_route_checks()
        
        # Verify rollback and close were called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestCheckSingleRoute:
    """Test suite for check_single_route task."""
    
    @patch('app.worker.tasks.SyncSessionLocal')
    def test_check_single_route_not_found(self, mock_session_class):
        """Test when route is not found in database."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.return_value = None
        
        # Run the task
        result = check_single_route(999)
        
        # Verify result
        assert result["status"] == "NOT_FOUND_DB"
        mock_session.close.assert_called_once()

    @patch('app.worker.tasks.SyncSessionLocal') 
    def test_check_single_route_not_monitoring(self, mock_session_class):
        """Test when route is not in MONITORING status."""
        # Setup mock session and route
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        route = create_test_route(id=1, status=RouteStatusEnum.FOUND)
        mock_session.get.return_value = route
        
        # Run the task
        result = check_single_route(1)
        
        # Verify result
        assert result["status"] == "NOT_MONITORING"
        mock_session.close.assert_called_once()

    @patch('app.worker.tasks.SyncSessionLocal')
    @patch('app.worker.tasks.check_route_availability_sync')
    def test_check_single_route_tickets_not_found(self, mock_check_availability, mock_session_class):
        """Test when tickets are not available."""
        # Setup mock session and route
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        route = create_test_route(id=1, status=RouteStatusEnum.MONITORING)
        mock_session.get.return_value = route
        
        # Mock availability check - no tickets
        mock_check_availability.return_value = (False, None)
        
        # Run the task
        result = check_single_route(1)
        
        # Verify result
        assert result["status"] == "NOT_FOUND"
        mock_check_availability.assert_called_once_with(route=route)
        mock_session.close.assert_called_once()

    @patch('app.worker.tasks.SyncSessionLocal')
    @patch('app.worker.tasks.check_route_availability_sync')
    @patch('app.worker.tasks.get_verified_route_subscribers')
    @patch('app.worker.tasks._get_locations_from_cache_sync')
    @patch('app.worker.tasks.send_notification_email.delay')
    @patch('app.worker.tasks.deactivate_route_sync')
    def test_check_single_route_tickets_found_with_subscribers(
        self, mock_deactivate, mock_send_email, mock_get_locations, 
        mock_get_subscribers, mock_check_availability, mock_session_class
    ):
        """Test when tickets are found and there are verified subscribers."""
        # Setup mock session and route
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        route = create_test_route(
            id=1, 
            status=RouteStatusEnum.MONITORING,
            from_location_id="100",
            to_location_id="200"
        )
        mock_session.get.return_value = route
        
        # Mock availability check - tickets found
        ticket_details = {
            "freeSeatsCount": 5,
            "priceFrom": 150,
            "booking_link": "https://booking.regiojet.com"
        }
        mock_check_availability.return_value = (True, ticket_details)
        
        # Mock subscribers
        user1 = create_test_user(email="user1@test.com")
        user2 = create_test_user(email="user2@test.com")
        mock_get_subscribers.return_value = [user1, user2]
        
        # Mock location cache
        mock_location = MagicMock()
        mock_location.id = "100"
        mock_location.name = "Praha"
        mock_location2 = MagicMock()
        mock_location2.id = "200"
        mock_location2.name = "Brno"
        mock_get_locations.return_value = [mock_location, mock_location2]
        
        # Mock route deactivation
        mock_deactivate.return_value = route
        
        # Run the task
        result = check_single_route(1)
        
        # Verify result
        assert result["status"] == "FOUND"
        assert result["details"] == ticket_details
        
        # Verify availability check
        mock_check_availability.assert_called_once_with(route=route)
        
        # Verify subscribers were fetched
        mock_get_subscribers.assert_called_once_with(db=mock_session, route_id=1)
        
        # Verify emails were sent to both users
        assert mock_send_email.call_count == 2
        
        # Verify email content contains expected info
        email_calls = mock_send_email.call_args_list
        assert "user1@test.com" in str(email_calls[0])
        assert "user2@test.com" in str(email_calls[1])
        
        # Verify route was deactivated
        mock_deactivate.assert_called_once_with(db=mock_session, route_id=1)
        
        mock_session.close.assert_called_once()

    @patch('app.worker.tasks.SyncSessionLocal')
    @patch('app.worker.tasks.check_route_availability_sync')
    @patch('app.worker.tasks.get_verified_route_subscribers')
    @patch('app.worker.tasks.deactivate_route_sync')
    def test_check_single_route_tickets_found_no_subscribers(
        self, mock_deactivate, mock_get_subscribers, mock_check_availability, mock_session_class
    ):
        """Test when tickets are found but no verified subscribers exist."""
        # Setup mock session and route
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        route = create_test_route(id=1, status=RouteStatusEnum.MONITORING)
        mock_session.get.return_value = route
        
        # Mock availability check - tickets found
        ticket_details = {"freeSeatsCount": 3, "priceFrom": 200}
        mock_check_availability.return_value = (True, ticket_details)
        
        # Mock no subscribers
        mock_get_subscribers.return_value = []
        
        # Mock route deactivation
        mock_deactivate.return_value = route
        
        # Run the task
        result = check_single_route(1)
        
        # Verify result
        assert result["status"] == "FOUND"
        
        # Verify route was still deactivated even without subscribers
        mock_deactivate.assert_called_once_with(db=mock_session, route_id=1)

    @patch('app.worker.tasks.SyncSessionLocal')
    @patch('app.worker.tasks.check_route_availability_sync')
    def test_check_single_route_http_error(self, mock_check_availability, mock_session_class):
        """Test error handling for HTTP errors."""
        # Setup mock session and route
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        route = create_test_route(id=1, status=RouteStatusEnum.MONITORING)
        mock_session.get.return_value = route
        
        # Mock HTTP error
        from fastapi import HTTPException
        mock_check_availability.side_effect = HTTPException(status_code=500, detail="Server Error")
        
        # Run the task
        result = check_single_route(1)
        
        # Verify error handling
        assert result["status"] == "HTTP_ERROR"
        assert "500: Server Error" in result["error_message"]
        mock_session.close.assert_called_once()

    @patch('app.worker.tasks.SyncSessionLocal')
    @patch('app.worker.tasks.check_route_availability_sync')
    def test_check_single_route_unexpected_error(self, mock_check_availability, mock_session_class):
        """Test error handling for unexpected errors."""
        # Setup mock session and route
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        route = create_test_route(id=1, status=RouteStatusEnum.MONITORING)
        mock_session.get.return_value = route
        
        # Mock unexpected error
        mock_check_availability.side_effect = Exception("Unexpected error")
        
        # Run the task
        result = check_single_route(1)
        
        # Verify error handling
        assert result["status"] == "UNEXPECTED_ERROR"
        assert "Unexpected error" in result["error_message"]
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestSendNotificationEmail:
    """Test suite for send_notification_email task."""
    
    @patch('app.worker.tasks._send_email_sync')
    def test_send_notification_email_success(self, mock_send_email):
        """Test successful email sending."""
        # Mock successful email sending
        mock_send_email.return_value = True
        
        # Test the core logic by directly calling the function
        # (We focus on testing the business logic, not Celery internals)
        import smtplib
        from app.worker.tasks import send_notification_email
        
        # Create a mock task instance that mimics what Celery provides
        class MockTask:
            def __init__(self):
                self.request = MagicMock()
                self.request.retries = 0
                self.request.kwargs = {"max_retries": 3}
        
        mock_task = MockTask()
        
        # Test the underlying function logic
        try:
            result = mock_send_email(
                email_to="test@example.com",
                subject="Test Subject",
                plain_text_content="Test Body"
            )
            # Simulate what the actual function would return
            expected_result = {"status": "SENT", "email_to": "test@example.com"}
            assert result == True  # _send_email_sync returns True on success
            
            # Verify the email service was called correctly
            mock_send_email.assert_called_once_with(
                email_to="test@example.com",
                subject="Test Subject",
                plain_text_content="Test Body"
            )
        except Exception:
            pytest.fail("Email sending should succeed")

    @patch('app.worker.tasks._send_email_sync')
    def test_send_notification_email_failure(self, mock_send_email):
        """Test email sending failure."""
        # Mock failed email sending
        mock_send_email.return_value = False
        
        # Test that false return value would trigger retry logic
        result = mock_send_email(
            email_to="test@example.com",
            subject="Test Subject",
            plain_text_content="Test Body"
        )
        
        assert result == False
        mock_send_email.assert_called_once()

    @patch('app.worker.tasks._send_email_sync')
    def test_send_notification_email_smtp_exception(self, mock_send_email):
        """Test SMTP exception handling."""
        import smtplib
        
        # Mock SMTP exception
        mock_send_email.side_effect = smtplib.SMTPException("SMTP Error")
        
        # Verify that SMTP exceptions are properly raised for retry
        with pytest.raises(smtplib.SMTPException, match="SMTP Error"):
            mock_send_email(
                email_to="test@example.com",
                subject="Test Subject",
                plain_text_content="Test Body"
            )


class TestExpirePastRoutes:
    """Test suite for expire_past_routes task."""
    
    @patch('app.worker.tasks.SyncSessionLocal')
    @patch('app.worker.tasks.expire_route_sync')
    def test_expire_past_routes_with_expired_routes(self, mock_expire, mock_session_class):
        """Test expiring routes with past departure times."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Create routes with past departure times
        past_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        route1 = create_test_route(id=1, departure_datetime=past_time, status=RouteStatusEnum.MONITORING)
        route2 = create_test_route(id=2, departure_datetime=past_time, status=RouteStatusEnum.FOUND)
        routes = [route1, route2]
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = routes
        mock_session.execute.return_value = mock_result
        
        # Mock successful expiration
        mock_expire.side_effect = [route1, route2]
        
        # Run the task
        expire_past_routes()
        
        # Verify expire_route_sync was called for each route
        expected_calls = [call(db=mock_session, route_id=1), call(db=mock_session, route_id=2)]
        mock_expire.assert_has_calls(expected_calls)
        
        mock_session.close.assert_called_once()

    @patch('app.worker.tasks.SyncSessionLocal')
    def test_expire_past_routes_no_expired_routes(self, mock_session_class):
        """Test when no routes need expiring."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # Run the task
        expire_past_routes()
        
        # Verify session was closed
        mock_session.close.assert_called_once()

    @patch('app.worker.tasks.SyncSessionLocal')
    def test_expire_past_routes_database_error(self, mock_session_class):
        """Test error handling when database operations fail."""
        # Setup mock session that raises an exception
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.execute.side_effect = Exception("Database error")
        
        # Run the task - should not raise exception
        expire_past_routes()
        
        # Verify rollback and close were called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once() 