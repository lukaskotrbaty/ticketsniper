from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import settings

class BasicAuthBackend(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username_attempt = form.get("username")
        password_attempt = form.get("password")

        # Check username first
        if username_attempt != settings.SQL_ADMIN_USERNAME:
            return False

        # Compare plain text password from form with plain text password from settings
        if password_attempt == settings.SQL_ADMIN_PASSWORD:
            request.session.update({"admin_token": "logged_in"})
            return True
        
        return False

    async def logout(self, request: Request) -> bool:
        request.session.pop("admin_token", None)
        # SQLAdmin itself handles clearing its own session parts if necessary
        return True

    async def authenticate(self, request: Request) -> bool:
        return "admin_token" in request.session

# SQLAdmin requires a secret key for session management.
# Reusing settings.SECRET_KEY (used for JWT) is acceptable.
authentication_backend = BasicAuthBackend(secret_key=settings.SECRET_KEY)
