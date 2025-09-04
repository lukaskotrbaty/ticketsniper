from pydantic_settings import BaseSettings
from pydantic import computed_field, ConfigDict # Import computed_field for dynamic URL generation

class Settings(BaseSettings):
    # --- Database Configuration ---
    POSTGRES_USER: str = "test"
    POSTGRES_PASSWORD: str = "test"
    POSTGRES_DB: str = "app_db"
    POSTGRES_PORT: int = 5432 # Default PostgreSQL port

    @computed_field # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        # Construct the database URL using the provided components
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@db:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # --- Redis Configuration ---
    REDIS_BASE_URL: str = "redis://redis:6379" # Base URL without DB number
    REDIS_DB_CACHE: int = 0
    REDIS_DB_BROKER: int = 0
    REDIS_DB_RESULT: int = 1
    LOCATION_CACHE_TTL_SECONDS: int = 60 * 60 * 24 # 24 hours default

    @computed_field # type: ignore[misc] # Pydantic v2 computed field
    @property
    def REDIS_URL(self) -> str:
        return f"{self.REDIS_BASE_URL}/{self.REDIS_DB_CACHE}"

    # --- Celery Configuration ---
    # Broker and Result backend URLs are now computed fields
    ROUTE_AVAILABILITY_CHECK_SCHEDULE_INTERVAL_SECONDS: int = 60
    ROUTE_EXPIRATION_CHECK_SCHEDULE_INTERVAL_SECONDS: int = 300

    @computed_field # type: ignore[misc]
    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"{self.REDIS_BASE_URL}/{self.REDIS_DB_BROKER}"

    @computed_field # type: ignore[misc]
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"{self.REDIS_BASE_URL}/{self.REDIS_DB_RESULT}"

    # --- Application URL Configuration ---
    FRONTEND_URL: str = "https://ticketsniper.eu"

    # Regiojet API Configuration
    REGIOJET_API_BASE_URL: str = "https://brn-ybus-pubapi.sa.cz/restapi"
    REGIOJET_BOOKING_BASE_URL: str = "https://regiojet.cz/"

    # JWT Configuration
    SECRET_KEY: str = "a_very_secret_key_that_should_be_in_env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    EMAIL_CONFIRMATION_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 day
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30 # Added for password reset

    # --- SMTP Configuration ---
    # The confirmation URL base is now derived from FRONTEND_URL
    SMTP_HOST: str | None = "smtp.seznam.cz"
    SMTP_PORT: int = 465 # Seznam uses SSL on port 465
    SMTP_USER: str | None = None # Set via .env or environment variable
    SMTP_PASSWORD: str | None = None # Set via .env or environment variable
    SMTP_TLS: bool = False # Use SSL instead of STARTTLS for port 465
    SMTP_SSL: bool = True  # Added setting for explicit SSL control
    EMAILS_FROM_EMAIL: str = "ticket.catcher@seznam.cz" # Sender address (should match user)

    @computed_field # type: ignore[misc]
    @property
    def EMAIL_CONFIRMATION_URL_BASE(self) -> str:
        # Ensures no double slashes if FRONTEND_URL ends with /
        return f"{self.FRONTEND_URL.rstrip('/')}/confirm-email"

    # CORS Configuration (example)
    CORS_ORIGINS: list[str] = []

    # --- SQL Admin Configuration ---
    SQL_ADMIN_USERNAME: str = None
    SQL_ADMIN_PASSWORD: str = None

    model_config = ConfigDict(
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields from env file
    )

# Create a single instance of the settings to be used throughout the application
settings = Settings()
