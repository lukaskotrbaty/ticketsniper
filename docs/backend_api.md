# Backend API Architecture (FastAPI)

This document describes the architecture of the backend part of the application built on the FastAPI framework in Python.

## 1. Technologies and Libraries

*   **Framework:** FastAPI
*   **Server:** Uvicorn
*   **Database ORM:** SQLAlchemy (with async support via `asyncio` and `AsyncSession`)
*   **Data Validation:** Pydantic (integrated in FastAPI)
*   **Asynchronous Tasks:** Celery with Redis as broker
*   **Authentication:** JWT (using `python-jose`) and FastAPI `Security` utilities (`OAuth2PasswordBearer`)
*   **HTTP Client:** HTTPX (for asynchronous external API calls)
*   **Caching:** Redis (for caching RJ API data)
*   **Email:** `smtplib`, `email.mime`
*   **Configuration:** Pydantic `BaseSettings` (for loading from env variables), or library like `python-dotenv`.
*   **CORS:** FastAPI `CORSMiddleware`

## 2. Project Structure (Current)

```text
/app
|-- api/              # API endpoints (routers)
|   |-- __init__.py
|   |-- api.py        # Main API router (aggregates others)
|   |-- deps.py       # Dependencies for endpoints (e.g., get current user, DB session)
|   |-- endpoints/    # Individual files with endpoints
|   |   |-- __init__.py
|   |   |-- auth.py
|   |   |-- data.py     # Router for data like locations
|   |   |-- routes.py   # Router for routes and monitoring
|-- core/             # Basic configuration and utilities
|   |-- __init__.py
|   |-- config.py     # Configuration loading (DB URL, JWT secret, SMTP...)
|   |-- security.py   # Functions for JWT, password hashing
|-- db/               # Database logic
|   |-- __init__.py
|   |-- base.py       # Base model class
|   |-- session.py    # SQLAlchemy session factory
|   |-- crud/         # Functions for CRUD operations (Create, Read, Update, Delete)
|   |   |-- __init__.py
|   |   |-- crud_user.py
|   |   |-- crud_route.py
|   |-- models/       # SQLAlchemy models (User, MonitoredRoute, ...)
|   |   |-- __init__.py
|   |   |-- user.py
|   |   |-- route.py
|-- schemas/          # Pydantic schemas for API request/response validation
|   |-- __init__.py
|   |-- user.py
|   |-- route.py
|   |-- token.py
|   |-- location.py   # Schema for locations
|   |-- available_route.py # Schema for available connections
|-- services/         # Business logic and interactions with external services
|   |-- __init__.py
|   |-- email_service.py # Email sending
|   |-- regiojet_api_client.py # Client for calling Regiojet API (HTTPX)
|   |-- regiojet_data_parser.py # Parser for Regiojet API responses
|   |-- regiojet_data_service.py    # Getting locations and connection lists from RJ API
|   |-- regiojet_checker_service.py # Checking availability of specific connection from RJ API
|-- worker/           # Configuration and tasks for Celery
|   |-- celery_app.py # Instance and configuration of Celery
|   |-- tasks.py      # Definition of Celery tasks (check_single_route, etc.)
|-- test/             # Tests
|   |-- auth_tests.http # HTTP requests for manual auth testing
|   |-- conftest.py   # Pytest configuration and fixtures
|   |-- api/
|   |   |-- endpoints/
|   |       |-- test_data.py
|   |       |-- test_routes.py
|   |-- fixtures/     # Test data
|   |   |-- available_routes.json
|   |   |-- locations.json
|   |-- services/
|   |   |-- test_regiojet_data_parser.py
|   |   |-- test_regiojet_data_service.py
|-- __init__.py
|-- Dockerfile
|-- main.py           # FastAPI application entry point (instance creation, router attachment, middleware)
|-- requirements.txt
|-- .env              # Configuration file (must not be in git!)
|-- .env.example      # Example configuration file
```

## 3. API Endpoints

All endpoints will be prefixed e.g., `/api/v1`.

### 3.1 Authentication (`/auth`)

*   **`POST /auth/register`**
    *   Request Body: `schemas.UserCreate` (email, password)
    *   Response: `201 Created` (or `200 OK`) with confirmation message.
    *   Action: Creates inactive user, sends confirmation email.
*   **`GET /auth/confirm/{token}`**
    *   Path Parameter: `token` (string)
    *   Response: `200 OK` with success/failure message.
    *   Action: Verifies token, activates user.
*   **`POST /auth/login`**
    *   Request Body: `OAuth2PasswordRequestForm` (username=email, password)
    *   Response: `schemas.Token` (access_token, token_type)
    *   Action: Verifies user, returns JWT token.
*   **`GET /auth/me`** (Requires authentication)
    *   Response: `schemas.User` (information about logged-in user)
    *   Action: Returns data of currently logged-in user (obtained from JWT).

### 3.2 Data Retrieval (`/data`)

*   **`GET /data/locations`** (Does not require authentication)
    *   Query Parameter: `query: Optional[str] = None` (for autocomplete filtering)
    *   Response: `List[schemas.Location]` (where `Location` contains `id`, `name`, `type`. For stations (`type='STATION'`) the `name` field contains value from `fullname` from Regiojet API if it exists, otherwise `name`.)
    *   Action: Calls `RegiojetDataService` (with header `X-Lang: cs`) to get (cached) locations, filters by `query`.

### 3.3 Route Monitoring (`/routes`)

*   **`GET /routes/available`** (Requires authentication)
    *   Query Parameters: `from_id: str`, `to_id: str`, `from_type: str`, `to_type: str`, `date: date`
    *   Response: `List[schemas.AvailableRoute]` (where `AvailableRoute` contains `routeId`, `departureTime`, `arrivalTime`, `freeSeatsCount`, `vehicleTypes`, `fromStationId`, `toStationId`) or error (e.g., 503 if RJ API fails).
    *   Action: Calls `RegiojetDataService` (with header `X-Lang: cs`) to get list of connections for given day and route. Internally filters results from RJ API to contain only connections with departure date matching specified `date`.
*   **`POST /routes/monitor`** (Requires authentication)
    *   Request Body: `schemas.RouteMonitorRequest` (must contain `regiojet_route_id` and other route details).
    *   Response: `201 Created` with `schemas.MessageResponse` (e.g., `{"message": "Monitoring request saved successfully."}`). *Note: Availability check and returning `available: bool` is planned for Task 10.*
    *   Action: Validates data. Calls `crud.route.get_or_create_monitored_route` using `regiojet_route_id`. Creates `user_route_subscriptions` (or returns existing).
*   **`GET /routes/monitored`** (Requires authentication)
    *   Response: `List[schemas.MonitoredRouteInfo]` (list of routes monitored by user, including status `is_active`, `found_at`, `created_at` and **location names** `from_location_name`, `to_location_name`).
    *   Action: Returns list of routes that current user is monitoring (active and inactive). Gets location names from cache.
*   **`DELETE /routes/monitor/{subscription_id}`** (Future feature)
    *   Path Parameter: `subscription_id` (ID of record in `user_route_subscriptions`)
    *   Response: `204 No Content`
    *   Action: Cancels user's monitoring of given route. If was last one, may deactivate route in `monitored_routes`.

## 4. Key Modules and Services

*   **`core/config.py`:** Loads settings (DB URL, JWT secret, SMTP host/port/user/pass, Redis URL, Regiojet API base URL, check interval) from environment variables.
*   **`core/security.py`:** Functions for JWT and passwords.
*   **`core/caching.py`:** (Optional, currently implemented locally in regiojet_data_service.py, would be nice to create separate file for this utility). Utility for easier Redis cache work (get/set with TTL).
*   **`db/`:** SQLAlchemy models (`db/models/`), CRUD functions (`db/crud/`), session factory (`db/session.py`).
*   **`api/deps.py`:** Dependencies for FastAPI (e.g., `get_current_active_user`, `get_db_session`, `get_redis_client`).
*   **`schemas/`:** Pydantic models for API contracts (request/response).
*   **`services/email_service.py`:** Email sending.
*   **`services/regiojet_api_client.py`:** Low-level client for communication with Regiojet API using HTTPX. Handles basic HTTP requests and responses.
*   **`services/regiojet_data_parser.py`:** Responsible for parsing complex JSON responses from Regiojet API into structured Pydantic models or Python objects.
*   **`services/regiojet_data_service.py`:** Responsible for getting data from RJ API that serves for user selection (locations, connection lists). Uses `RegiojetApiClient` and `RegiojetDataParser`. Uses Redis for location caching.
*   **`services/regiojet_checker_service.py`:** Responsible for checking availability of *specific* connection on RJ API (including time, classes, fares). Uses `RegiojetApiClient` and `RegiojetDataParser`. Used both for initial check in `/monitor` (Task 10) and for periodic checks in Celery worker.
*   **`services/monitoring_service.py`:** (Currently not implemented) Higher level logic for monitoring management (coordination with CRUD and checker service within `/monitor` endpoint). Logic is currently directly in endpoint.
*   **`worker/`:** Celery configuration (`celery_app.py`) and asynchronous task definitions (`tasks.py`) (use `RegiojetCheckerService` and `EmailService`).

## 5. Authentication and Authorization

*   Uses standard `OAuth2PasswordBearer` flow with JWT tokens.
*   Token contains `sub` (user ID) and `exp` (expiration time).
*   Passwords are stored in database as hashes (using `passlib`).
*   Endpoints requiring login use dependency `Depends(get_current_active_user)` to verify token and get user.
*   Standard OAuth2 with JWT. Endpoints `/data/locations` are public, others in `/routes` require authentication.

## 6. Error Handling

*   Standard FastAPI validation error handling (422).
*   Custom `exception_handlers` for errors like `NotFound` (404), RJ API communication errors (e.g., 503 Service Unavailable), email sending errors, etc.