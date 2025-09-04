# Makes 'models' a subpackage
# Import models to make them accessible via db.models.<ModelName>
from .user import User
from .route import MonitoredRoute, UserRouteSubscription
