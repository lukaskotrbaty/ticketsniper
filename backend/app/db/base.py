from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here for Alembic/create_all discovery
from app.db.models.user import User # noqa # Corrected import (relative to /code)
from app.db.models.route import MonitoredRoute, UserRouteSubscription # noqa # Corrected import (relative to /code)
